import json
from flask import Flask, Response, after_response

app              = Flask(__name__)
after_response(app)

@app.route('/')
def get():
    # print(json.dumps({"connect":"connect", "network_quality": "net_quality", "earnings": "net_earn"}))
    # resp = Response(json_module = )
    # @resp.call_on_close
    # def _():
    #     print("hello")
    return {"connect":"connect", "network_quality": "net_quality", "earnings": "net_earn"}

@app.after_response
def foo():
    print("hello")
    return 

if __name__ == '__main__':
    app.run(host='localhost',port=3000, debug=False)
