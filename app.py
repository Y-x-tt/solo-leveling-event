import os, json, time, secrets, threading
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-before-deploying')
DATA_FILE = os.getenv('DATA_FILE', 'event_data.json')
DATA_LOCK = threading.Lock()
ADMIN_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '8571408433')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

QUIZ = [
 {"q":"في أنمي هجوم العمالقة، ما اسم الفيلق المسؤول غالبًا عن الاستكشاف خارج الأسوار؟","a":["فيلق الشرطة العسكرية","فيلق الاستطلاع","فيلق الحامية"],"c":1},
 {"q":"في ون بيس، ما اسم فاكهة لوفي؟","a":["غومو غومو","ميرا ميرا","أوب أوب"],"c":0},
 {"q":"في ناروتو، ما اسم القرية التي ينتمي إليها ناروتو؟","a":["قرية الرمل","قرية الضباب","قرية الورق"],"c":2},
 {"q":"في ديث نوت، ما اسم الشينيغامي المرتبط بدفتر لايت؟","a":["ريم","ريوك","جيلوس"],"c":1},
 {"q":"في ديمون سلاير، ما أسلوب التنفس الذي يستخدمه زينيتسو؟","a":["الرعد","الماء","الصخر"],"c":0},
 {"q":"في هنتر × هنتر، ما نوع النين الذي يتقنه غون غالبًا؟","a":["التجسيد","التعزيز","التحويل"],"c":1},
 {"q":"في جوجوتسو كايسن، من معلم يوجي إيتادوري؟","a":["نانامي","غوجو ساتورو","ميغومي"],"c":1},
 {"q":"في فول ميتال ألكيميست، ما الثمن الذي دفعه الأخوان في محاولتهما لإحياء أمهما؟","a":["فقدان أجزاء من جسديهما","فقدان الذاكرة فقط","خسارة أموالهما"],"c":0},
 {"q":"في سباي × فاميلي، ما القدرة التي تمتلكها آنيا؟","a":["قراءة الأفكار","رؤية المستقبل","الاختفاء"],"c":0},
 {"q":"في بليتش، ما الاسم الذي يُطلق على السيف الروحي للشينيغامي؟","a":["زانباكتو","كايجو","نينبو"],"c":0},
 {"q":"في دراغون بول، ما التحول الأشهر الذي يصل إليه غوكو لأول مرة ضد فريزا؟","a":["سوبر سايان","ألترا إنستينكت","سوبر سايان بلو"],"c":0},
 {"q":"في طوكيو غول، ما اسم المقهى الذي يرتاده كانيكي؟","a":["أنتيكو","دوناتو","كوكوريا"],"c":0},
 {"q":"في بليو لوك، ما الهدف الأساسي من مشروع بلو لوك؟","a":["صناعة أفضل حارس مرمى","صناعة مهاجم ياباني أناني من الطراز الأول","تدريب منتخب كامل في شهر"],"c":1},
 {"q":"في هايكيو!!، ما مركز شويو هيناتا الأساسي؟","a":["معدّ","ليبرو","ضارب أوسط"],"c":2},
 {"q":"في كاكيغوروي، ما الذي يحدد المكانة داخل أكاديمية هياكاو غالبًا؟","a":["نتائج المقامرة والديون","الدرجات الدراسية فقط","القوة البدنية"],"c":0},
 {"q":"في سولو ليفلينغ، ما الرتبة التي صُنّف بها سونغ جين وو في البداية؟","a":["A","E","C"],"c":1},
 {"q":"في المحقق كونان، ما اسم كونان الحقيقي؟","a":["شينيتشي كودو","هيجي هاتوري","كaito كيد"],"c":0},
 {"q":"في أكاديمية بطلي، ما اسم قدرة تودوروكي الأساسية؟","a":["انفجار","نصف بارد ونصف ساخن","نسخ القدرات"],"c":1},
 {"q":"في موب سايكو 100، ما موهبة موب الأساسية؟","a":["التحكم في الزمن","القوى النفسية","التحول إلى وحش"],"c":1},
 {"q":"في ناروتو، ما اسم أخ ساسكي الأكبر؟","a":["شيسوي","مادارا","إيتاتشي"],"c":2}
]

CASE = {
 "title":"القضية 07: اختفاء الختم الأزرق",
 "intro":"اختفى ختم أزرق نادر من غرفة الأرشيف بين الساعة 8:10 و8:35 مساءً. الغرفة لم تُظهر آثار كسر. أمامك إفادات وسجلات متعارضة؛ استنتج من أخذ الختم، وكيف، وما القرينة الحاسمة. هذه قضية خيالية بالكامل.",
 "docs":[
  ("المستند A — سجل الباب","الباب فُتح ببطاقة الموظف (م-14) الساعة 8:18، ثم فُتح من الداخل الساعة 8:31. لا توجد محاولة كسر مسجلة."),
  ("المستند B — إفادة الحارس","يقول الحارس إنه رأى نادرًا قرب الممر الساعة 8:20، لكنه يقر بأنه كان يراجع شاشة كاميرا أخرى وقتها."),
  ("المستند C — رسالة الصيانة","وصل طلب صيانة الساعة 7:55 بسبب تعطل ساعة الحائط. كُتب في الطلب: «الوقت الظاهر متأخر 12 دقيقة»."),
  ("المستند D — إيصال","إيصال آلة المشروبات باسم سلمى، الساعة 8:27، لكنه يحمل توقيت الجهاز المحلي لا توقيت الخادم."),
  ("المستند E — ملاحظة صغيرة","على رف الملفات غبار متصل، عدا مستطيل نظيف بحجم صندوق الختم. وُجدت قصاصة تقول: «لا تثق بالوقت المكتوب وحده»."),
  ("المستند F — إفادات","نادر يقول إنه غادر المبنى 8:15. سلمى تقول إنها دخلت الأرشيف بعد 8:30 لإعادة ملف. الموظف (م-14) يقول إن بطاقته كانت معه طوال المساء.")
 ],
 "solution":"الحل المقصود: لا تكفي الأدلة لتسمية الجاني بثقة. بطاقة م-14 فُتحت بها الغرفة، لكن ادعاء صاحبها أنها كانت معه يخلق احتمال استعارة البطاقة أو كذب الإفادة. اختلاف الساعة 12 دقيقة يجعل الإيصال والإفادات غير قابلة للمقارنة مباشرة. القرينة الحاسمة الناقصة هي سجل الكاميرات الأصلي أو سجل موقع البطاقة؛ أفضل استنتاج جنائي هو إبقاء القضية غير محسومة وطلب دليل إضافي، لا اتهام شخص من قرينة واحدة."
}

def load_data():
    if not os.path.exists(DATA_FILE): return {"users": {}, "submissions": [], "ai_posts": []}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return {"users": {}, "submissions": [], "ai_posts": []}

def save_data(d):
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def notify(text):
    if not BOT_TOKEN or not ADMIN_CHAT_ID: return False
    try:
        r = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', json={"chat_id": ADMIN_CHAT_ID, "text": text}, timeout=8)
        return r.ok
    except Exception: return False

def current_user(data=None):
    if not session.get('username'): return None
    d = data if data is not None else load_data()
    return d['users'].get(session['username'])

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        if len(username) < 2 or len(username) > 40:
            flash('اكتب اسم حساب كونايو بشكل صحيح (من حرفين إلى 40 حرفًا).','error')
            return redirect(url_for('index'))
        with DATA_LOCK:
            d = load_data()
            if username not in d['users']:
                d['users'][username] = {"joined": datetime.now(timezone.utc).isoformat(), "quiz_done": False, "score": None, "faction": None, "immortals_points": 0}
                save_data(d)
                notify(f"🆕 تسجيل فعالية\nاسم كونايو: {username}\nالوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    u = current_user()
    if not u: return redirect(url_for('index'))
    d = load_data()
    completed = sorted([x['score'] for x in d['users'].values() if x.get('quiz_done') and x.get('score') is not None], reverse=True)
    rank = (completed.index(u['score']) + 1) if u.get('quiz_done') and u.get('score') in completed else None
    light = sum(1 for x in d['users'].values() if x.get('faction') == 'light')
    dark = sum(1 for x in d['users'].values() if x.get('faction') == 'dark')
    total = light + dark
    faction_percent = {"light": round(light*100/total) if total else 50, "dark": round(dark*100/total) if total else 50}
    return render_template('dashboard.html', user=session['username'], u=u, rank=rank, faction_percent=faction_percent)

@app.route('/quiz')
def quiz():
    u = current_user()
    if not u: return redirect(url_for('index'))
    if u.get('quiz_done'):
        flash('أكملت الاختبار بالفعل. لا يمكن إعادته.','error'); return redirect(url_for('dashboard'))
    safe = [{"q":x['q'],"a":x['a']} for x in QUIZ]
    return render_template('quiz.html', questions=safe)

@app.route('/api/quiz/finish', methods=['POST'])
def quiz_finish():
    u = current_user()
    if not u: return jsonify(ok=False, error='سجّل الدخول أولًا.'), 401
    with DATA_LOCK:
        d = load_data(); u = d['users'].get(session['username'])
        if not u: return jsonify(ok=False, error='الحساب غير موجود.'), 404
        if u.get('quiz_done'): return jsonify(ok=False, error='تم تسجيل محاولة سابقة.'), 409
        payload = request.get_json(silent=True) or {}
        answers = payload.get('answers', [])
        start = payload.get('started_at', 0)
        if not isinstance(answers, list) or len(answers) != len(QUIZ): return jsonify(ok=False, error='بيانات الاختبار غير مكتملة.'), 400
        # Server-side elapsed-time guard; the client also enforces 15 seconds/question.
        try: elapsed = max(0, time.time() - float(start))
        except Exception: elapsed = 0
        if elapsed < 10: return jsonify(ok=False, error='تم إرسال الاختبار بسرعة غير طبيعية.'), 400
        score = 0
        for i, ans in enumerate(answers):
            try:
                if int(ans) == QUIZ[i]['c']: score += 1
            except (ValueError, TypeError): pass
        u['quiz_done'] = True; u['score'] = score; u['quiz_finished'] = datetime.now(timezone.utc).isoformat()
        save_data(d)
        notify(f"🧩 انتهى اختبار الأنمي\nكونايو: {session['username']}\nالنتيجة: {score}/20")
        scores = sorted([x['score'] for x in d['users'].values() if x.get('quiz_done') and x.get('score') is not None], reverse=True)
        rank = scores.index(score) + 1
    return jsonify(ok=True, score=score, rank=rank, total=len(scores))

@app.route('/faction', methods=['POST'])
def faction():
    u = current_user()
    if not u: return redirect(url_for('index'))
    choice = request.form.get('choice')
    if choice not in ('light','dark','immortals'): return redirect(url_for('dashboard'))
    with DATA_LOCK:
        d = load_data(); u = d['users'][session['username']]
        if u.get('faction'):
            flash('اختيار الفصيل لا يمكن تغييره بعد التأكيد.','error'); return redirect(url_for('dashboard'))
        u['faction'] = choice
        if choice == 'immortals': u['immortals_points'] = 10
        save_data(d)
    labels = {'light':'النور','dark':'الظلام','immortals':'الخالدين'}
    notify(f"⚔️ اختيار فصيل\nكونايو: {session['username']}\nالفصيل: {labels[choice]}")
    if choice == 'immortals': flash('تهانينا! انضممت إلى فصيل الخالدين وحصلت على 10 نقاط.','success')
    else: flash(f'تم تسجيل انضمامك إلى فصيل {labels[choice]}.','success')
    return redirect(url_for('dashboard'))

@app.route('/case', methods=['GET','POST'])
def case_page():
    u = current_user()
    if not u: return redirect(url_for('index'))
    if request.method == 'POST':
        answer = request.form.get('answer','').strip()
        if len(answer) < 10:
            flash('اكتب استنتاجك بتفصيل أكبر قليلًا.','error'); return redirect(url_for('case_page'))
        msg = f"🕵️ حل القضية الجنائية\nكونايو: {session['username']}\nالحل:\n{answer}"
        ok = notify(msg)
        with DATA_LOCK:
            d = load_data(); d['submissions'].append({"username":session['username'],"answer":answer,"time":datetime.now(timezone.utc).isoformat()}); save_data(d)
        flash('تم إرسال استنتاجك إلى الإدارة.' if ok else 'تم حفظ استنتاجك، لكن إشعار تيليجرام لم يصل. تأكد الإدارة من إعدادات البوت.','success')
        return redirect(url_for('case_page'))
    return render_template('case.html', case=CASE)

@app.route('/break', methods=['POST'])
def break_room():
    u = current_user()
    if not u: return redirect(url_for('index'))
    reply = request.form.get('reply','').strip(); consent = request.form.get('consent') == 'yes'
    if not reply:
        flash('اكتب رد الذكاء الاصطناعي أولًا.','error'); return redirect(url_for('dashboard'))
    if consent:
        with DATA_LOCK:
            d = load_data(); d['ai_posts'].append({"username":session['username'],"reply":reply,"time":datetime.now(timezone.utc).isoformat()}); save_data(d)
        notify(f"🌿 رد AI بموافقة صاحبه\nكونايو: {session['username']}\n{reply[:3000]}")
        flash('تم تسجيل الرد للنشر بموافقتك.','success')
    else:
        flash('لم يتم نشر الرد لأنك لم توافق.','success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
