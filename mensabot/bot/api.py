import datetime as dtm

from flask import Flask, jsonify, request
from healthcheck import EnvironmentDump, HealthCheck

app = Flask(__name__)

health = HealthCheck(app, "/healthcheck")
envdump = EnvironmentDump(app, "/environment")


def json_version():
    from mensabot.format import get_version
    return get_version()


envdump.add_section("version", json_version)


@health.add_check
def tasks_running():
    from mensabot.bot.tasks import SCHED, SCHED_TASK_COUNT, task_name
    tasks = len(SCHED.queue)
    return tasks >= SCHED_TASK_COUNT, "%d tasks running: %s" % \
           (tasks, [task_name(task) for task in SCHED.queue])


@health.add_check
def tasks_alive():
    from mensabot.bot.tasks import SCHED, task_name

    offsets = {task_name(task): dtm.datetime.fromtimestamp(task.time) - dtm.datetime.now()
               for task in SCHED.queue}

    return min(offsets.values()) < dtm.timedelta(minutes=5), \
           {k: v.total_seconds() for k, v in offsets.items()}


@health.add_check
def mensa_api_reachable():
    from mensabot.mensa import cache
    week = dtm.date.today().isocalendar()[1]
    if week not in cache:
        return False, "current week's menu was never fetched"
    diff = dtm.datetime.now() - cache[week][0]
    return diff < dtm.timedelta(minutes=20), \
           "last menu update at %s, %d seconds ago" % (cache[week][0], diff.total_seconds())


@health.add_check
def telegram_api_reachable():
    from mensabot.bot.ext import bot
    diff = dtm.datetime.now() - bot.last_update
    return diff < dtm.timedelta(minutes=20), \
           "last telegram update at %s, %d seconds ago" % (bot.last_update, diff.total_seconds())


@app.route("/threads")
def dump_threads():
    import threading
    import sys
    from traceback import extract_stack, format_stack, StackSummary
    from html import escape

    def dump_stack(frames):
        stack = StackSummary.from_list(extract_stack(frames))
        return [{"filename": f.filename, "lineno": f.lineno, "name": f.name, "line": f.line,
                 "locals": {name: repr(value) for name, value in sorted(f.locals.items())} if f.locals else None}
                for f in stack]

    frames = sys._current_frames()
    main = threading.main_thread()

    best = request.accept_mimetypes.best_match(['application/json', 'text/html', 'text/plain'])

    if best == 'application/json':
        return jsonify(
            [{"name": t.name, "ident": t.ident, "is_alive": t.is_alive(), "daemon": t.daemon, "main": t == main,
              "stack": dump_stack(frames[t.ident])}
             for t in threading.enumerate()])
    else:
        text = "\n\n".join(
            "%s\n%s" % (str(t), "".join(reversed(format_stack(frames[t.ident])))) for t in threading.enumerate())
        if best == 'text/html':
            text = "<html><body><pre>%s</pre></body></html>" % escape(text)
        return text


@app.route("/schedule")
def json_schedule():
    from mensabot.bot.tasks import SCHED, task_name
    return jsonify([{"time": t.time, "priority": t.priority, "action": repr(t.action), "argument": t.argument,
                     "kwargs": t.kwargs, "name": task_name(t)}
                    for t in SCHED.queue])
