from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
training = False
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
stage = 1

TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>7碼預測器</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body style="max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;">
    <h2>7碼預測器</h2>
    <div style="margin-bottom: 8px;">版本：熱號2＋動熱2＋補碼3（公版UI）</div>
    <form method="POST">
      <input name="first" placeholder="冠軍" required style="width: 80%; padding: 8px;" inputmode="numeric" oninput="moveToNext(this, 'second')"><br><br>
      <input name="second" placeholder="亞軍" required style="width: 80%; padding: 8px;" inputmode="numeric" oninput="moveToNext(this, 'third')"><br><br>
      <input name="third" placeholder="季軍" required style="width: 80%; padding: 8px;" inputmode="numeric"><br><br>
      <button type="submit" style="padding: 10px 20px;">提交</button>
    </form>
    <br>
    <a href="/toggle"><button>{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button></a>
    <a href="/clear"><button>清除資料</button></a>

    {% if prediction %}
      <div style="margin-top: 20px;"><strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）</div>
    {% endif %}
    {% if last_prediction %}
      <div style="margin-top: 10px;"><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
    {% endif %}

    {% if training %}
      <div style="margin-top: 20px; text-align: left;">
        <strong>命中統計：</strong><br>
        冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
        熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
        動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
        補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
      </div>
    {% endif %}

    {% if history %}
      <div style="margin-top: 20px; text-align: left;">
        <strong>最近輸入紀錄：</strong>
        <ul>
          {% for row in history[-10:] %}
            <li>第 {{ loop.index }} 期：{{ row }}</li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    <script>
      function moveToNext(current, nextId) {
        setTimeout(() => {
          if (current.value === '0') current.value = '10';
          let val = parseInt(current.value);
          if (!isNaN(val) && val >= 1 && val <= 10) {
            document.getElementById(nextId)?.focus();
          }
        }, 100);
      }
    </script>
  </body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 3:
                prediction, hot, dynamic, extra = generate_prediction()
                predictions.append(prediction)

                if training:
                    total_tests += 1
                    champion = current[0]
                    if champion in prediction:
                        all_hits += 1
                        stage = 1
                    else:
                        stage += 1
                    if champion in hot:
                        hot_hits += 1
                    elif champion in dynamic:
                        dynamic_hits += 1
                    elif champion in extra:
                        extra_hits += 1
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        history=history,
        training=training,
        stage=stage,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, stage
    training = not training
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    stage = 1
    return redirect('/')

@app.route('/clear')
def clear():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, stage
    history.clear()
    predictions.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    stage = 1
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot = [n for n, _ in freq.most_common(3)][:2]
    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2]

    exclude = set(hot + dynamic)
    cold = {n for n in range(1, 11)} - set(flat)
    pool = [n for n in range(1, 11) if n not in exclude and n not in cold]
    random.shuffle(pool)
    extra = pool[:3]

    return sorted(hot + dynamic + extra), hot, dynamic, extra

if __name__ == '__main__':
    app.run(debug=True)
