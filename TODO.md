- Telegram Bot
    - let users change their configuration
    - let users register for automatic menu notification at a certain time
    - lookup abbreviations regarding marked ingredients and split abbreviation table
    - `/cafete`
        - handle edge-case location "mensaessen" -> rename to "open"?
- Formatting
    - nothing left to do
- Mensa API
    - use [better website](http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/)
        for `get_semester_dates`
    - clear caches from time to time
    - add nikolakloster menu
    - add menu from other locations? -> set default location
    - warn about holidays when determining the default mensa date, e.g. by checking for business days with empty menus: 
        `if np.busday_count(def_dt.date(), dt.date()) != 0:`
