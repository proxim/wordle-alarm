import json
import uuid

from flask import Flask, render_template, request, abort, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from werkzeug.middleware.proxy_fix import ProxyFix

from utils import (
    set_finished,
    get_game_answer,
    word_is_valid,
    id_or_400,
    get_answer_info,
    get_random_answer,
)
from sql import get_sql
from playsound import playsound
from alarm import Alarm

# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

base_url = '/api/v1'

app = Flask(__name__)
app.config.from_object(Config())
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
CORS(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
)

# initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)

alarm = Alarm(armed=True)

def api_response(json_data):
    resp = make_response(json.dumps(json_data))
    resp.content_type = "application/json; charset=utf-8"
    return resp


@app.context_processor
def inject_debug():
    return dict(debug=app.debug)


# Frontend views
@app.route("/")
def index():
    return render_template("index.html")


# API endpoints
@app.route(f'{base_url}/start_game/', methods=["POST"])
@limiter.limit("4/second;120/minute;600/hour;4000/day")
def start_game():
    """
    Starts a new game
    """
    word_id = None
    try:
        word_id = int(request.json["wordID"])
    except (KeyError, TypeError, ValueError):
        pass

    con, cur = get_sql()

    key = str(uuid.uuid4())

    if word_id:
        word = get_answer_info(word_id)
    else:
        word_id, word = get_random_answer()

    cur.execute("""INSERT INTO game (word, key) VALUES (?, ?)""", (word, key))
    con.commit()
    con.close()

    return api_response({"id": cur.lastrowid, "key": key, "wordID": word_id})


@app.route(f'{base_url}/guess/', methods=["POST"])
def guess_word():
    guess = request.get_json(force=True)["guess"]
    # validate guess
    if not (len(guess) == 5 and guess.isalpha() and word_is_valid(guess)):
        return abort(400, "Invalid word")
    # retrieve game id
    game_id = id_or_400(request)

    con, cur = get_sql()
    cur.execute(
        """SELECT word, guesses, finished FROM game WHERE id = (?)""", (game_id,)
    )
    answer, guesses, finished = cur.fetchone()

    guesses = guesses.split(",")

    if len(guesses) > 6 or finished:
        return abort(403)

    guesses.append(guess)
    guesses = ",".join(guesses)

    if guesses[0] == ",":
        guesses = guesses[1:]

    cur.execute("""UPDATE game SET guesses = (?) WHERE id = (?)""", (guesses, game_id))
    con.commit()
    con.close()

    guess_status = [{"letter": g_char, "state": 0} for g_char in guess]
    guessed_pos = set()

    for a_pos, a_char in enumerate(answer):
        if a_char == guess[a_pos]:
            guessed_pos.add(a_pos)
            guess_status[a_pos] = {
                "letter": guess[a_pos],
                "state": 2,
            }

    for g_pos, g_char in enumerate(guess):
        if g_char not in answer or guess_status[g_pos]["state"] != 0:
            continue

        positions = []
        f_pos = answer.find(g_char)
        while f_pos != -1:
            positions.append(f_pos)
            f_pos = answer.find(g_char, f_pos + 1)

        for pos in positions:
            if pos in guessed_pos:
                continue
            guess_status[g_pos] = {
                "letter": g_char,
                "state": 1,
            }
            guessed_pos.add(pos)
            break
    # if guess is correct then disarm and turn off the alarm
    all_correct = True
    for letter in guess_status:
        if letter.get('state') != 2:
            all_correct = False
    if all_correct:
        alarm.disarm()
        alarm.deactivate()
    
    return api_response(guess_status)


@app.route(f'{base_url}/finish_game/', methods=["POST"])
def finish_game():
    game_id = id_or_400(request)
    set_finished(game_id)
    answer = get_game_answer(game_id)

    return api_response({"answer": answer})

@app.route(f'{base_url}/alarm_time/', methods=['GET'])
def get_alarm_time():
    return api_response({'alarmTime': alarm.time})

@app.route(f'{base_url}/alarm_state/', methods=['GET'])
def get_alarm_state():
    alarm_state = '🚨ARMED' if alarm.is_armed else '💤DISARMED'
    return api_response({'alarmState': alarm_state})


@scheduler.task('cron', id='trigger_alarm', hour=8, minute=30)
def trigger_alarm():
    print('trigger_alarm:')
    if alarm.is_armed:
        alarm.activate()
        # play wake up sound
        playsound('sfx/wakeup.mp3')

    else:
        print('alarm was disarmed, not activating')

@scheduler.task('cron', id='rearm_alarm', hour=4, minute=0)
def rearm_alarm():
    print('rearm_alarm:')
    if not alarm.is_armed:
        alarm.arm()
    else:
        print('alarm was already armed')

scheduler.start()

if __name__ == '__main__':    
    app.run()
