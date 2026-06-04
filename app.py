from flask import Flask, render_template_string, request, session, redirect, url_for
from groq import Groq
import json, time, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pcmb_secret_123")

CHAPTERS = {
    "Physics": {
        "11": ["Units and Measurements", "Motion in a Straight Line", "Motion in a Plane",
               "Laws of Motion", "Work, Energy and Power", "System of Particles and Rotational Motion",
               "Gravitation", "Mechanical Properties of Solids", "Mechanical Properties of Fluids",
               "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
        "12": ["Electric Charges and Fields", "Electrostatic Potential and Capacitance",
               "Current Electricity", "Moving Charges and Magnetism", "Magnetism and Matter",
               "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves",
               "Ray Optics and Optical Instruments", "Wave Optics",
               "Dual Nature of Radiation and Matter", "Atoms", "Nuclei", "Semiconductor Electronics"]
    },
    "Chemistry": {
        "11": ["Some Basic Concepts of Chemistry", "Structure of Atom",
               "Classification of Elements and Periodicity in Properties",
               "Chemical Bonding and Molecular Structure", "Chemical Thermodynamics",
               "Equilibrium", "Redox Reactions",
               "Organic Chemistry: Some Basic Principles and Techniques", "Hydrocarbons"],
        "12": ["Solutions", "Electrochemistry", "Chemical Kinetics",
               "d- and f-Block Elements", "Coordination Compounds",
               "Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers",
               "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules"]
    },
    "Maths": {
        "11": ["Sets", "Relations and Functions", "Trigonometric Functions",
               "Complex Numbers and Quadratic Equations", "Linear Inequalities",
               "Permutations and Combinations", "Binomial Theorem", "Sequences and Series",
               "Straight Lines", "Conic Sections", "Introduction to Three Dimensional Geometry",
               "Limits and Derivatives", "Statistics", "Probability"],
        "12": ["Relations and Functions", "Inverse Trigonometric Functions", "Matrices",
               "Determinants", "Continuity and Differentiability", "Application of Derivatives",
               "Integrals", "Application of Integrals", "Differential Equations",
               "Vector Algebra", "Three Dimensional Geometry", "Linear Programming", "Probability"]
    },
    "Biology": {
        "11": ["The Living World", "Biological Classification", "Plant Kingdom",
               "Morphology of Flowering Plants", "Anatomy of Flowering Plants",
               "Structural Organisation in Animals", "Cell: The Unit of Life",
               "Biomolecules", "Cell Cycle and Cell Division", "Transport in Plants",
               "Mineral Nutrition", "Photosynthesis in Higher Plants", "Respiration in Plants",
               "Plant Growth and Development", "Breathing and Exchange of Gases",
               "Body Fluids and Circulation", "Excretory Products and their Elimination",
               "Locomotion and Movement", "Neural Control and Coordination", "Chemical Coordination and Integration"],
        "12": ["Sexual Reproduction in Flowering Plants", "Human Reproduction", "Reproductive Health",
               "Principles of Inheritance and Variation", "Molecular Basis of Inheritance",
               "Evolution", "Human Health and Disease", "Microbes in Human Welfare",
               "Biotechnology: Principles and Processes", "Biotechnology and its Applications",
               "Organisms and Populations"]
    }
}

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PCMB AI Test - CBSE 2026-27</title>
<style>
body{font-family:Arial;padding:12px;background:#0e1117;color:#fff}
input,select,button{width:100%;padding:10px;margin:6px 0;border-radius:8px;border:none;font-size:15px}
button{background:#4CAF50;color:white;font-weight:bold;cursor:pointer}
.tab{display:flex;gap:5px;flex-wrap:wrap}
.tab button{flex:1;background:#262730;min-width:48%}
.tab button.active{background:#4CAF50}
.box{background:#262730;padding:12px;border-radius:10px;margin:10px 0}
.exp{background:#1a1d23;padding:10px;border-left:4px solid #4CAF50;margin-top:8px;border-radius:5px}
.timer{float:right;background:#ff9800;padding:4px 8px;border-radius:5px;font-weight:bold}
.correct{color:#4CAF50;font-weight:bold}
.wrong{color:#f44336;font-weight:bold}
.reset{background:#f44336;}
label{font-size:13px;color:#aaa;margin-top:5px;display:block}
.loading{color:#ff9800;text-align:center;padding:20px}
</style>
<script>
const chaptersData = {{chapters|tojson}};
let timeLeft = {{time_left}};
let timer;
function startTimer(){
  if(timeLeft <= 0) return;
  timer = setInterval(()=>{
    timeLeft--;
    let el = document.getElementById('timer');
    if(el) el.innerText = 'Time: ' + timeLeft + 's';
    if(timeLeft <= 0){clearInterval(timer);document.getElementById('autoSubmit')?.click();}
  }, 1000);
}
function updateChapters(){
  const sub = document.getElementById('sub').value;
  const cls = document.getElementById('cls').value;
  const chap = document.getElementById('chap');
  chap.innerHTML = '';
  const list = chaptersData[sub]?.[cls] || [];
  list.forEach(c=>{
    const opt = document.createElement('option');
    opt.value = c;
    opt.text = c;
    chap.add(opt);
  });
}
window.onload = function(){
  startTimer();
  updateChapters();
}
</script>
</head>
<body>
<h2>PCMB AI Test <span class="timer" id="timer">Time: {{time_left}}s</span></h2>
<p style="font-size:11px;color:#aaa">Syllabus: CBSE 2026-27</p>

{% if not started %}
<form method="post">
  <input type="password" name="key" placeholder="Groq API Key" value="{{api_key_val}}" required>
  <button type="submit" name="reset" class="reset">Reset API Key</button>

  <select name="sub" id="sub" onchange="updateChapters()">
    {% for s in subjects %}<option value="{{s}}" {% if s==sub %}selected{% endif %}>{{s}}</option>{% endfor %}
  </select>

  <select name="cls" id="cls" onchange="updateChapters()">
    <option value="11" {% if cls=='11' %}selected{% endif %}>Class 11</option>
    <option value="12" {% if cls=='12' %}selected{% endif %}>Class 12</option>
  </select>

  <select name="chap" id="chap"></select>

  <label>Difficulty</label>
  <div class="tab">
    {% for d in ['Easy','Medium','Hard','Extreme'] %}
    <button type="submit" name="diff" value="{{d}}" class="{% if diff==d %}active{% endif %}">{{d}}</button>
    {% endfor %}
  </div>

  <label>Question Type</label>
  <select name="qtype">
    <option value="Mixed" {% if qtype=='Mixed' %}selected{% endif %}>Mixed</option>
    <option value="MCQ" {% if qtype=='MCQ' %}selected{% endif %}>MCQ Only</option>
    <option value="Numerical" {% if qtype=='Numerical' %}selected{% endif %}>Numerical Only</option>
  </select>

  <label>No. of Questions (1-20)</label>
  <input type="number" name="n" value="{{n_val}}" min="1" max="20" required>

  <label>Time per Question in Seconds (30-300)</label>
  <input type="number" name="t" value="{{t_val}}" min="30" max="300" required>

  <button type="submit" name="start">Start Test</button>
  {% if generating %}
  <div class="loading">Generating questions... Please wait 10-20s for Extreme mode</div>
  {% endif %}
</form>

{% if history %}
<div class="box"><b>Recent Scores</b>
{% for h in history %}<p>{{h.sub}} Class {{h.cls}} - {{h.chap}}: {{h.score}}/{{h.total}} - {{h.diff}}</p>{% endfor %}
</div>
{% endif %}
{% endif %}

{% if q %}
<div class="box">
  <p><b>Q{{idx}}/{{total}} [{{q['type']}} | {{q['marks']}}M]:</b> {{q['q']}}</p>
  {% if not show_exp %}
    <form method="post" id="qform">
      {% if q['type'] == 'MCQ' %}
        {% for opt in q['options'] %}
        <input type="radio" name="ans" value="{{loop.index0}}" required> {{opt}}<br>
        {% endfor %}
      {% else %}
        <input type="text" name="ans" placeholder="Enter answer" required>
      {% endif %}
      <button type="submit" name="submit">Submit</button>
      <button type="submit" name="autoSubmit" id="autoSubmit" style="display:none"></button>
    </form>
  {% else %}
    <p class="{% if correct %}correct{% else %}wrong{% endif %}">
      {{ 'Correct!' if correct else 'Wrong!' }}<br>
      Answer: {{q['options'][q['answer']] if q['type']=='MCQ' else q['answer']}}
    </p>
    <div class="exp"><b>Solution:</b><br>{{q['exp']|safe}}</div>
    <form method="post"><button type="submit" name="next">Next</button></form>
  {% endif %}
</div>
{% endif %}

{% if score is defined and not q %}
<h3>Score: {{score}}/{{total}}</h3>
<a href="/"><button>New Test</button></a>
{% endif %}
</body>
</html>
"""

def gen_q(client, sub, cls, chap, diff, qtype, n):
    if diff == "Extreme":
        n = min(n, 8)
        max_tokens = 1200
        question_length = "Keep each question under 70 words. No long paragraphs."
    else:
        max_tokens = 2000
        question_length = ""

    diff_guide = {
        "Easy": "NCERT level only. Direct questions from NCERT text. 1-2 marks.",
        "Medium": "CBSE Board level. Application based as per CBSE pattern. 2-4 marks.",
        "Hard": "NEET and JEE Mains level. Tricky, multi-step, concept-based. Include traps. 3-5 marks.",
        "Extreme": """JEE Advanced level - BRUTAL but concise.
- Multi-concept problems spanning 2-3 chapters.
- Heavy calculations but keep question under 70 words.
- Include traps and edge cases. Only 10-15% students should solve it.
- 4-6 marks per question."""
    }
    qtype_dist = "40% MCQ, 30% Numerical, 30% Assertion-Reason" if qtype=="Mixed" else qtype

    prompt = f"""You are an IIT examiner. Generate {n} questions for CBSE Class {cls} {sub}, Chapter: {chap}.
Follow ONLY the CBSE 2026-27 syllabus.
Difficulty: {diff} - {diff_guide[diff]}.
{question_length}
Type: {qtype_dist}.
Return ONLY valid JSON array. No markdown, no explanation outside JSON.
Format: [{{"type":"MCQ","q":"question","options":["A","B","C","D"],"answer":0,"exp":"detailed solution","marks":2}}]"""

    models = ["llama-3.1-70b-versatile", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

    for attempt in range(2):
        for model in models:
            try:
                r = client.chat.completions.create(
                    model=model,
                    messages=[{"role":"user","content":prompt}],
                    temperature=0.1,
                    max_tokens=max_tokens,
                    timeout=60
                )
                text = r.choices[0].message.content.strip()
                if text.startswith("```"):
                    text = text.split("```")[1].replace("json", "").strip()
                start = text.find('[')
                end = text.rfind(']') + 1
                if start!= -1 and end!= 0:
                    data = json.loads(text[start:end])
                    if len(data) > 0:
                        return data
            except:
                continue
        time.sleep(2)
    return []

@app.route("/", methods=["GET","POST"])
def home():
    subjects = list(CHAPTERS.keys())
    sub = request.form.get("sub", session.get("sub", "Physics"))
    cls = request.form.get("cls", session.get("cls", "11"))
    chapters = CHAPTERS.get(sub, {}).get(cls, [])
    diff = request.form.get("diff", session.get("diff", "Extreme"))
    qtype = request.form.get("qtype", session.get("qtype", "Mixed"))
    n_val = request.form.get("n", session.get("n", 8))
    t_val = request.form.get("t", session.get("t", 120))
    api_key_val = session.get("key", "")
    history = session.get("history", [])
    generating = False

    if request.method == "POST" and "reset" in request.form:
        session.pop("key", None)
        return redirect(url_for("home"))

    if request.method == "POST" and "start" in request.form:
        key = request.form["key"].strip()
        if key and chapters:
            for k in ["qs", "idx", "score", "show_exp", "last_correct", "time_left"]:
                session.pop(k, None)
            session["key"], session["sub"], session["cls"], session["chap"] = key, sub, cls, request.form["chap"]
            session["diff"], session["qtype"] = diff, qtype
            session["n"], session["t"] = int(request.form["n"]), int(request.form["t"])
            session["idx"], session["score"], session["time_left"] = 0, 0, session["t"]
            client = Groq(api_key=key)
            generating = True
            qs = gen_q(client, sub, cls, session["chap"], diff, qtype, session["n"])
            generating = False
            session["qs"] = qs
            return redirect(url_for("home"))

    if request.method == "POST" and "ans" in request.form and "qs" in session:
        idx = session["idx"]
        if idx < len(session["qs"]):
            q = session["qs"][idx]
            user_ans = request.form["ans"]
            correct = int(user_ans) == q["answer"] if q["type"]=="MCQ" else str(q["answer"]).lower().strip() in str(user_ans).lower().strip()
            session["last_correct"], session["show_exp"] = correct, True
            if correct: session["score"] += q.get("marks", 1)
        return redirect(url_for("home"))

    if request.method == "POST" and "next" in request.form:
        session["idx"] += 1
        session["show_exp"], session["time_left"] = False, session["t"]
        return redirect(url_for("home"))

    if "qs" in session and session["idx"] < len(session["qs"]):
        q = session["qs"][session["idx"]]
        return render_template_string(HTML, started=True, q=q, idx=session["idx"]+1,
            total=len(session["qs"]), show_exp=session.get("show_exp", False),
            correct=session.get("last_correct", False), time_left=session.get("time_left", 60),
            subjects=subjects, sub=sub, cls=cls, chapters=CHAPTERS, diff=diff, qtype=qtype,
            history=history, api_key_val=api_key_val, n_val=n_val, t_val=t_val, generating=generating)

    if "qs" in session and session["idx"] >= len(session["qs"]):
        total_marks = sum(q.get("marks",1) for q in session["qs"])
        h = {"sub": session["sub"], "cls": session["cls"], "chap": session["chap"],
             "score": session["score"], "total": total_marks, "diff": session["diff"]}
        session["history"] = [h] + history[:3]
        for k in ["qs", "idx", "show_exp", "last_correct", "time_left"]:
            session.pop(k, None)
        return render_template_string(HTML, started=True, score=session["score"],
            total=total_marks, q=None, subjects=subjects, sub=sub, cls=cls,
            chapters=CHAPTERS, diff=diff, qtype=qtype, history=session["history"],
            time_left=0, api_key_val=api_key_val, n_val=n_val, t_val=t_val, generating=False)

    return render_template_string(HTML, started=False, subjects=subjects, sub=sub, cls=cls,
        chapters=CHAPTERS, diff=diff, qtype=qtype, history=history,
        time_left=60, api_key_val=api_key_val, n_val=n_val, t_val=t_val, generating=generating)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
