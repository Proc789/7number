from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
training = False
stage = 1
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
total_hits = 0
total_tests = 0

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>7碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>7碼預測器</h2>
  <div style='margin-bottom: 8px;'>版本：熱號2 + 動熱2 + 補碼3（公版UI）</div>
  <form method='POST'>
    <input name='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="jump(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="jump(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button></a>
  <a href='/clear'><button>清除資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'><strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）</div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ total_hits }} / {{ total_tests }}<br>
      熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
      動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
      補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
    </div>
  {% endif %}

  <div style='margin-top: 20px; text-align: left;'>
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history_data %}
        <li>第 {{ loop.index }} 期：{{ row }}</li>
      {% endfor %}
    </ul>
  </div>

<script>
function jump(current, nextId) {
  setTimeout(() => {
    if (current.value === '0') current.value = '10';
    let val = parseInt(current.value);
    if (!isNaN(val) && val >= 1 && val <= 10) {
      document.getElementById(nextId).focus();
    }
  }, 100);
}
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global training, stage, hot_hits, dynamic_hits, extra_hits, total_hits, total_tests

    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == "POST":
        try:
            first = int(request.form["first"])
            second = int(request.form["second"])
            third = int(request.form["third"])
            current = [10 if x == 0 else x for x in [first, second, third]]
            history.append(current)

            if len(predictions) >= 1:
                last = predictions[-1]
                if training:
                    total_tests += 1
                    if current[0] in last:
                        total_hits += 1
                        stage = 1
                    else:
                        stage += 1
                    # 命中分區統計
                    flat = history[-1]
                    if any(n in last[:2] for n in flat):
                        hot_hits += 1
                    if any(n in last[2:4] for n in flat):
                        dynamic_hits += 1
                    if any(n in last[4:] for n in flat):
                        extra_hits += 1

            if len(history) >= 5 or training:
                prediction = make_prediction()
                predictions.append(prediction)
        except:
            prediction = ["格式錯誤"]

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=stage,
        history_data=history[-10:],
        training=training,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        total_hits=total_hits,
        total_tests=total_tests)

@app.route("/toggle")
def toggle():
    global training, hot_hits, dynamic_hits, extra_hits, total_hits, total_tests, stage
    training = not training
    hot_hits = dynamic_hits = extra_hits = total_hits = total_tests = 0
    stage = 1
    return redirect("/")

@app.route("/clear")
def clear():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, total_hits, total_tests, stage
    history = []
    predictions = []
    hot_hits = dynamic_hits = extra_hits = total_hits = total_tests = 0
    stage = 1
    return redirect("/")

def make_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = Counter(flat)

    hot = [n for n, _ in freq.most_common(3)][:2]
    remain = [n for n in freq if n not in hot]
    dynamic = sorted(remain, key=lambda x: (-freq[x], -flat[::-1].index(x)))[:2]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]

    last_random = predictions[-1][4:] if len(predictions) > 0 else []
    for _ in range(10):
        extra = random.sample(pool, min(3, len(pool)))
        if len(set(extra) & set(last_random)) <= 2:
            return sorted(hot + dynamic + extra)

    return sorted(hot + dynamic + random.sample(pool, min(3, len(pool))))

if __name__ == "__main__":
    app.run(debug=True)
