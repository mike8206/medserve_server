from website import creat_app

app = creat_app()

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0',port=8443) #Turn False after finish
