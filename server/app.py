#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()

        try:
            new_user = User(
                username=data['username'],
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            new_user.password_hash = data['password']  

            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            
            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username already exists."]}, 422
        except Exception as e:
            return {"errors": [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio
                }, 200

        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()

        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }, 200

        return {"error": "Invalid username or password"}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return '', 204
        return {"error": "Unauthorized"}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401

        data = request.get_json()
        try:
            new_recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=user_id
            )

            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(), 201

        except Exception as e:
            return {"errors": [str(e)]}, 422

# Register resources
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5555, debug=True)
