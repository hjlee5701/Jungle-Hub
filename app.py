from flask import Flask, request, redirect, render_template, Response, current_app, jsonify, url_for
from flask_jwt_extended import JWTManager
from flask_restful import Api
import jwt as JWT

from config import Config

from jwtbreak import UserLogoutResource, jwt_blocklist

from user import UserRegisterResource, UserLoginResource

from flask_jwt_extended import decode_token, get_jwt_identity, jwt_required

from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://test:test@13.125.225.182',27017)
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
    parties = list(userdb.party.find({}))[:5]
    lbtn, sbtn,obtn = setUserArea(request)
    return render_template('index.html', lbtn=lbtn, sbtn=sbtn, obtn=obtn, parties=parties)


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

@app.route("/logout", methods=['get'])
def login():
    #채워야함
    return render_template('logout.html')


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

# @app.route("/users/protected")
# @jwt_required()
# def protected():
#     current_user_id = get_jwt_identity()
#     return jsonify(logged_in_as=current_user_id), 200




#전체 파티 리스트
@app.route('/party', methods=['GET'])
def party_list():
    option = 'default'
    partyList = list(userdb.party.find({}))
    # print(partyList)
    lbtn, sbtn, obtn = setUserArea(request)
    return render_template('partyList.html', lbtn=lbtn, sbtn=sbtn, obtn=obtn, partyList=partyList option=option)

# 파티 등록 페이지
@app.route('/party/register', methods=['GET'])
def getResistForm():
    result = validateToken(request.cookies)
    if(result["state"]):
        print(result['id'])

    else:
        print("실패")
        return redirect("/")
    
    lbtn, sbtn, obtn = setUserArea(request)
    return render_template('partyRegister.html', lbtn=lbtn, sbtn=sbtn, obtn=obtn)



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
    user = validateToken(request.cookies)
    userId = user['id']

    doc = {'title': title, 'people': people, 'startDate': startDate, 'endDate': endDate,
           "closeDate": closeDate, 'chatUrl': chatUrl, 'content': content, 'member': 0, 'userId': userId}
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



#파티 참가
@app.route('/join', methods=['POST'])
def joinParty():
    partyId = request.values['partyId']
    user = validateToken(request.cookies)
    userId = user['id']

    # 사용자가 참가 신청했던 상태인지 확인
    attendee = userdb.attendees.find_one({"$and": [{"partyId": partyId}, {"userId": userId}]})
    if attendee:
        # 이미 신청한 참가자
        return jsonify({'result': 'joined'})
    else:
        # 새로운 참가자 insert
        newAttendee = {'partyId': partyId, 'userId': userId }
        userdb.attendees.insert_one(newAttendee)

        # 참가 인원 update
        condition = {"_id": ObjectId(partyId)}

        plus_member = {"$inc": {"member": 1}}  # member 필드에 1을 더함
        userdb.party.update_one(condition, plus_member)

        return jsonify({'result': 'success'})



#파티 참가취소
@app.route('/cancel', methods=['POST'])
def cancelParty():
    partyId = request.values['partyId']
    user = validateToken(request.cookies)
    userId = user['id']
    # userdb.attendees.delete_many({"userId": '회원'})

    # 사용자가 참가 신청했던 상태인지 확인
    attendee = userdb.attendees.find_one({"$and": [{"partyId": partyId}, {"userId": userId}]})
    if attendee:
        # 참여 취소 delete
        userdb.attendees.delete_one({"$and": [{"partyId": partyId}, {"userId": userId}]})

        # 참가 인원 update
        condition = {"_id": ObjectId(partyId)}

        minus_member = {"$inc": {"member": -1}}  # member 필드에 1을 뺌
        userdb.party.update_one(condition, minus_member)

        return jsonify({'result': 'success'})
    else:
        # 조건에 맞는 데이터 삭제
        return jsonify({'result': 'notJoin'})


#파티장의 파티 리스트
@app.route('/mypage', methods=['GET'])
def host_list():
    result = validateToken(request.cookies)
    if(result['state'] == False):
        return redirect("/")

    userId = result['id']
    hostPartyList = list(userdb.party.find({'userId': userId}))

    lbtn, sbtn,obtn = setUserArea(request)
    return render_template('myPage.html', lbtn=lbtn, sbtn=sbtn, obtn=obtn, hostPartyList=hostPartyList, userId=userId)



#파티장의 파티 삭제
@app.route('/delete', methods=['POST'])
def delete_party():
    partyId = request.values['partyId']
    condition = {'_id': ObjectId(partyId)}

    userdb.party.delete_one(condition)
    return jsonify({'result': 'success'})



#파티장의 파티 수정 페이지로 데이터 전송
@app.route('/toupdate/<partyId>', methods=['GET','POST'])
def toUpdateParty(partyId):
    condition = {'_id': ObjectId(partyId)}  
    party = userdb.party.find_one(condition)

    return render_template('partyUpdate.html', party=party)

#파티 수정 기능
@app.route('/update', methods=['POST'])
def updateParty():
    modtitle = request.form['title']
    modpeople = request.form['people']
    modmember = request.form['member']
    modstartDate = request.form['startDate']
    modendDate = request.form['endDate']
    modcloseDate = request.form['closeDate']
    modchatUrl = request.form['chatUrl']
    modcontent = request.form['content']
    partyId = ObjectId(request.form['partyId'])

    userdb.party.update_one({'_id': partyId}, {'$set':{
        'title': modtitle, 'people': modpeople, 'member': modmember, 'startDate': modstartDate, 'endDate': modendDate,
        'closeDate': modcloseDate, 'chatUrl': modchatUrl, 'content': modcontent
    }})
    return jsonify({'result': 'success'})


#참가 등록한 파티 리스트
@app.route('/myparty', methods=['GET'])
def myParty():
    # attend
    user = validateToken(request.cookies)
    userId = user['id']
    parties = list(userdb.attendees.find({'userId': userId}, {'_id': False}))
    
    party_ids = [ObjectId(party['partyId']) for party in parties]
    
    # party 컬렉션에서 partyId 리스트와 일치하는 파티 데이터 검색
    partyList = list(userdb.party.find({'_id': {'$in': party_ids}}))
    print(len(partyList))
    lbtn, sbtn,obtn = setUserArea(request)
    return render_template('myParty.html',lbtn=lbtn, sbtn=sbtn,obtn=obtn, partyList=partyList, userId=userId)


#토큰 검증 함수
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
    
def setUserArea(request):
    result = validateToken(request.cookies)
    if(result["state"]):
        lbtn = 0
        sbtn = 0
        obtn = 1

    else:
        lbtn = 1
        sbtn = 1
        obtn = 0
    return lbtn, sbtn, obtn



if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)
