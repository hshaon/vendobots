# @app.route('/test/', methods=['GET'])
# def testAPI():
#     # You can return any JSON response here
#     rs = 0
#     for i in range(100):  # 0 to 10 inclusive
#         print(i)
#         rs += 1
#         time.sleep(1)
#     response = {
#         "status": "success",
#         "message": f"Test API is working! Value: {rs}"
#     }
#     return jsonify(response), 200
