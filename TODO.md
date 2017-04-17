- Telegram Bot
    - add UI for changing configuration
    - `/cafete`
        - handle edge-case location "mensaessen" -> rename to "open"?
    - evaluate user experience, input monkey testing for parsing exceptions
    - internationalize non-template strings
- Formatting
    - nothing left to do
- Mensa API
    - use [better website](http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/)
        for `get_semester_dates`
    - add nikolakloster menu
    - add menu from other locations? -> set default location
    - warn about holidays when determining the default mensa date, e.g. by checking for business days with empty menus: 
        `if np.busday_count(def_dt.date(), dt.date()) != 0:`
