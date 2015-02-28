import os, json, time
from flask import Flask, request, abort
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext.pymongo import PyMongo
from flask import make_response
from bson.json_util import dumps
from bson.objectid import ObjectId

current_milli_time = lambda: int(round(time.time() * 1000))

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/buttonlight')

app = Flask(__name__)

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)

def output_json(obj, code, headers=None):
    resp = make_response(dumps(obj), code)
    resp.headers.extend(headers or {})
    return resp

DEFAULT_REPRESENTATIONS = {'application/json': output_json}
api = restful.Api(app)
api.representations = DEFAULT_REPRESENTATIONS

class StatusList(restful.Resource):
    def __init__(self, *args, **kwargs):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('status', type=str)
        self.parser.add_argument('device_id', type=str)
        self.parser.add_argument('last', type=int)
        super(StatusList, self).__init__()

    def get(self):
        args = self.parser.parse_args()
        if args['device_id']:
            if args['last'] == 1:
                return [x for x in mongo.db.status.find({"device_id": args['device_id']}).sort("time", -1).limit(1) ]
            else:
                return [x for x in mongo.db.status.find({"device_id": args['device_id']})]
        else:
            if args['last'] == 1:
                raise NotImplementedError("find last time for each device_id ..")
            else:
                return [x for x in mongo.db.status.find()]

    def post(self):
        args = self.parser.parse_args()
        if not args['status'] or not args['device_id']: abort(400)
        status = int(args['status'])
        device_id = args['device_id']
        status_id =  mongo.db.status.insert({"time": current_milli_time(), "status": status, "device_id": device_id})
        return mongo.db.status.find_one({"_id": status_id})

class Status(restful.Resource):
    def get(self, status_id):
        return mongo.db.status.find_one_or_404({"_id": status_id})

    def delete(self, status_id):
        mongo.db.status.find_one_or_404({"_id": status_id})
        mongo.db.status.remove({"_id": status_id})
        return '', 204

class Root(restful.Resource):
    def get(self):
        return {
            'status': 'OK',
            'mongo': str(mongo.db),
        }

api.add_resource(Root, '/')
api.add_resource(StatusList, '/status/')
api.add_resource(Status, '/status/<ObjectId:status_id>')

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
