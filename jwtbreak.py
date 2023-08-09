from flask_restful import Resource
from flask_jwt_extended import get_jwt, jwt_required

jwt_blocklist = set()


class UserLogoutResource(Resource):
    # jwt_required : 토큰이 있어야 아래의 코드를 실행
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        print(jti)

        jwt_blocklist.add(jti)

        return {"result": "로그아웃이 정상처리되었습니다."}
