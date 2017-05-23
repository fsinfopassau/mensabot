- Telegram Bot
    - add [UI](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
        for changing and displaying configuration
    - `/cafete`
        - handle edge-case location "mensaessen" -> rename to "open"?
    - warn about holidays when determining the default mensa date, e.g. by checking for business days with empty menus:
        `if np.busday_count(def_dt.date(), dt.date()) != 0:`
    - evaluate user experience, input monkey testing for parsing exceptions
    - internationalize non-template strings
    - access logging
    - warn on parsing problems
         (e.g. "Hausgem. Pizza mit Schinken/Champignon oder Champignon(8,9,A,B,G,N,AA)"
               "Gemüsebrühe mit Kräuternockerl (3,A,C,I)/Rinderkraftbrühe mit Leberknödel")
    - trace problems with price being 0.00€ until a certain point in time or menu changing throughout the day
- Formatting
    - nothing left to do
- Mensa API
    - use [better website](http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/)
        for `get_semester_dates`
    - add nikolakloster menu
    - add menu from other locations? (and also semester dates?) -> set default location
- Benutzerbewertung mit Photo als Antwort
