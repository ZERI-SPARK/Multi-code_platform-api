import os
from flask import Flask, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS


from get_info import UserData, UsernameError, PlatformError, BrokenChangesError

app = Flask(__name__)
CORS(app)
api = Api(app)

class Details(Resource):
    def get(self, platform, username):
        user_data = UserData(username)
        try:
            return user_data.get_details(platform)
        except UsernameError:
            return jsonify({'status': 'Failed', 'details': 'Invalid username'})
        except PlatformError:
            return jsonify({'status': 'Failed', 'details': 'Invalid Platform'})
        except BrokenChangesError:
            return jsonify({'status': 'Failed', 'details': 'API broken due to site changes'})

api.add_resource(Details, '/api/<string:platform>/<string:username>')

@app.errorhandler(404)
def invalid_route(e):
    return jsonify({'status': 'Failed', 'details': 'Invalid route'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    # app.run()
