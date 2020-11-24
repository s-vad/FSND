import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, questions):
  page = request.args.get('page', 1, type=int)
  start = (page-1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE 
  
  formatted_questions = [question.format() for question in questions]
  current_questions = formatted_questions[start:end]

  return current_questions


def create_app(test_config=None):
  
  # create and configure the app 
  app = Flask(__name__)
  setup_db(app)

  #CORS setup
  cors = CORS(app, resources={r"/*": {"origin": "*"}})

  # CORS Headers 
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  @app.route('/categories')
  def get_categories():
    try:
      data = Category.query.order_by(Category.id).all()

      categories = {}
      for category in data:
        categories[category.id] = category.type

      return jsonify({
        'success': True,
        'categories': categories,
        'total_categories': len(categories)
      })
    except:
      abort(500)

  '''
  @DONE: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():

    #get questions
    questions = Question.query.order_by(Question.id).all()
    total_questions = len(questions)
    current_questions = paginate_questions(request, questions)

    # abort 404 if no questions
    if (len(current_questions) == 0):
        abort(404)

    #get categories
    data = Category.query.order_by(Category.id).all()
    categories = {}
    for category in data:
      categories[category.id] = category.type

    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions,
        'categories': categories
    })

  '''
  @DONE: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:id>', methods=['GET','DELETE'])
  def delete_question(id):
    try:
      question = Question.query.get(id)

      if question is None:
        abort(404)

      question.delete()
      
      return jsonify({
        'success': True,
        'deleted': id
      })
    except:
      abort(422)

  '''
  @DONE: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    try:

      data = request.get_json()

      question = data['question']
      answer = data['answer']
      category = data['category']
      difficulty = data['difficulty']

      if (question == None or question == '' or answer == None or answer == '' or category == None or category == ''  or difficulty == None or difficulty == ''):
        abort(422)

      question = Question(
        question = question,
        answer = answer,
        category=category,
        difficulty=difficulty
      )

      question.insert()
    
      return jsonify({
          "success": True,
          "created": question.format()
      })

    except:
      abort(422)

  '''
  @DONE: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['GET','POST'])
  def search_questions():
    data = request.get_json()

    #search_term = 'Africa'
    if(data['searchTerm']):
      search_term = data['searchTerm']

    questions = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
    
    if questions==[]:
      abort(404)

    current_questions = paginate_questions(request, questions)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(current_questions)
    })

  '''
  @DONE: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions', methods=['GET'])
  def get_question_by_category(id):
    category = Category.query.get(id)

    if (category is None):
      abort(404)

    try:
      questions = Question.query.filter_by(category=category.id).all()
      
      current_questions = paginate_questions(request, questions)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'current_category': category.type,
        'total_questions': len(questions)
      })
    except:
      abort(500)

  '''
  @DONE: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_quiz_question():

    data = request.get_json()
    category = data['quiz_category']
    previous_questions = data['previous_questions']

    if ((category is None) or (previous_questions is None)):
      abort(422)

    if category['id'] != 0:
      question = Question.query.filter(Question.category == category['id'], Question.id.notin_(previous_questions)).first()
    else:
      question = Question.query.filter(Question.id.notin_(previous_questions)).first()

    return jsonify({
        "success": True,
        "question": question.format() if question != None else None
    })

  '''
  @DONE: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'Bad request'
    }), 400

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'Resource not found.'
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422, 
      'message': 'Unable to process. Invalid input...'
    }), 422

  @app.errorhandler(500)
  def internal_server_error(error):
      return jsonify({
          'success': False,
          'error': 500,
          'message': 'Internal Server Error. Please try later...'
      }), 500
  
  return app

    