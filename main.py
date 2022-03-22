from website import creat_app

app = creat_app()

if __name__ == '__main__':
    app.run(debug=False,port=8443) #Turn False after finish
