from flask import Flask, request, redirect, render_template, Response, current_app, jsonify
from flask_jwt_extended import JWTManager
from flask_restful import Api
import jwt as JWT

from config import Config

from jwtbreak import UserLogoutResource, jwt_blocklist

from user import UserRegisterResource, UserLoginResource

from flask_jwt_extended import decode_token, get_jwt_identity, jwt_required

from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('localhost', 27017)
userdb = client.userdb

# API 서버를 구축하기 위한 기본 구조
app = Flask(__name__)


# 환경변수 셋팅
app.config.from_object(Config)  # 만들었던 Config.py의 Config 클래스 호출

# JWT 토큰 생성
jwt = JWTManager(app)


# 로그아웃 된 토큰이 들어있는 set을 jwt에게 알림
@jwt.token_in_blocklist_loader
def check_it_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

# restfulAPI 생성
api = Api(app)

# 경로와 리소스(api코드) 연결
api.add_resource(UserRegisterResource, '/users/register') # 회원가입
api.add_resource(UserLoginResource, '/users/login') # 로그인
# 경로와 리소스(api코드) 연결
api.add_resource(UserLogoutResource, '/users/logout')  # 로그아웃

@app.route('/')
def home():  # put application's code here

    return render_template('index.html')


@app.route("/main", methods=['GET'])
def show_main():
    access_token = request.headers.get("Authorization")
    print(access_token)
    if access_token is not None:
        try:
            payload = JWT.decode_key_loader(access_token, current_app.config["JWT_SECRET_KEY"], "HS256")
        except JWT.InvalidTokenError:
                payload = None
	
        if payload is None:
            return Response(status=401)
        
        user_id = payload["user_id"]
        # g.user_id = user_id
        # g.user = get_user_info(user_id) if user_id else None
        print(user_id)
    else:
        return Response(status=401)
    

    return render_template('main.html')

@app.route("/show_login_page", methods=['GET'])
def show_login_page():
    return render_template('login.html')

@app.route("/show_user_register_page", methods=['GET'])
def show_user_register_page():
    return render_template('sigin.html')

# @app.route("/login", methods=['POST'])
# def login():
#     #채워야함
#     return render_template('login.html')

# @app.route("/signin", methods=['POST'])
# def register():
#     #채워야함
    
#     return render_template('login.html')

@app.route("/test", methods=['GET'])
def test():
    result = validateToken(request.cookies)
    if(result["state"]):
        print(result['id'])
        isvalid = "성공"

    else:
        print("실패")
        isvalid = "실패"
        
    return render_template('testPage.html', jwtstate=isvalid)


@app.route("/users/protected")
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify(logged_in_as=current_user_id), 200














#전체 파티 리스트
@app.route('/party', methods=['GET'])
def party_list():
    partyList = list(userdb.party.find({}))
    print(partyList)
    return render_template('partyList.html', partyList=partyList)

#회원 파티 리스트
@app.route('/myparty', methods=['GET'])
def my_list():
    # userInfo = userdb.userList.find_one({'userId': 'ididid'},{'_id':False})
    # myPartyList = list(userdb.partyList.find({'userId': userInfo.userId},{'_id':False}))
    myPartyList = list(userdb.userList.find({'userId': 'ididid'},{'_id':False}))
    return render_template('myParty.html', myPartyList=myPartyList)


# 파티 페이지
@app.route('/party/register', methods=['GET'])
def getResistForm():
    return render_template('partyRegister.html')



# 파티 생성 함수
@app.route('/party/register', methods=['POST'])
def makeParty():
    title = request.form['title']
    people = request.form['people']
    startDate = request.form['startDate']
    endDate = request.form['endDate']
    closeDate = request.form['closeDate']
    chatUrl = request.form['chatUrl']
    content = request.form['content']
    # print(title)
    # print(people)
    # print(time)
    # print(startDate)
    # print(endDate)
    # print(closeDate)
    # print(chatUrl)
    # print(content)


    doc = {'title': title, 'people': people, 'startDate': startDate, 'endDate': endDate,
           "closeDate": closeDate, 'chatUrl': chatUrl, 'content': content, 'member': 0}
    userdb.party.insert_one(doc)
    return jsonify({'result': 'success'})



#파티 상세
@app.route('/detail/<partyId>', methods=['GET','POST'])
def getPartyDetail(partyId):
    print(partyId)
    partyDetail = userdb.party.find_one({'_id': ObjectId(partyId)},{'_id':False})
    partyDetail['_id']= partyId
    print(partyDetail)
    return render_template('partyDetail.html', partyDetail=partyDetail)










def validateToken(cookies):
    print("토큰검증")
    access_token = cookies.get("access_token")
    if access_token is not None:
        # print(get_jwt_identity())
        if access_token is not None:
            try:
                payload = decode_token(access_token)
                print(payload)  
                return {"state": True, "id": payload["sub"]}
            except JWT.InvalidTokenError:
                    return {"state": False}
    else:
         return {"state": False}

if __name__ == '__main__':
    app.run()
