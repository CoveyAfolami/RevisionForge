import anki_connect as ac

def main():
    print("Hello. Revision!")

    deck_names = ac.get_deck_names()

    request = ac.build_deck_names_request()
    #print("Request:", request)

    response = ac.send_request(request)
    print(response)

if __name__ == "__main__":
    main()


    

