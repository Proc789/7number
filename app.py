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
total_tests = 0
stage = 1

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>7碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>7碼預測器</h2>
  <div>版本：熱號2 + 動熱2 + 補碼3（公版UI）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉訓練模式' if training else '啟動訓練模式' }}</button></a>
  <a href='/clear'><button>清除資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
  {% endif %}
  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ hot_hits + dynamic_hits + extra_hits }} / {{ total_tests }}<br>
      熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
      動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
      補碼命中次數：{{ extra_hits }} / {{ total_tests }}
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
    function moveToNext(current, nextId) {
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

@app.route('/', methods=['GET', 'POST'])
def index():
    global training, hot_hits, dynamic_hits, extra_hits, total_tests, stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(predictions) >= 1:
                last = predictions[-1]
                if first in last:
                    if training:
                        stage = 1
                        hot_hits += int(first in last[:2])
                        dynamic_hits += int(first in last[2:4])
                        extra_hits += int(first in last[4:])
                        total_tests += 1
                else:
                    if training:
                        stage += 1
                        total_tests += 1

            if len(history) >= 5 or training:
                prediction = make_prediction()
                predictions.append(prediction)
            else:
                prediction = ['請輸入至少五期']
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=stage,
        training=training,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        total_tests=total_tests,
        history_data=history[-10:])

@app.route('/toggle')
def toggle():
    global training, hot_hits, dynamic_hits, extra_hits, total_tests, stage
    training = not training
    if training:
        hot_hits = dynamic_hits = extra_hits = total_tests = 0
        stage = 1
    return redirect('/')

@app.route('/clear')
def clear():
    global history, predictions, training, hot_hits, dynamic_hits, extra_hits, total_tests, stage
    history = []
    predictions = []
    training = False
    hot_hits = dynamic_hits = extra_hits = total_tests = 0
    stage = 1
    return redirect('/')

def make_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot_pool = sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))[:3]
    hot = [n for n, _ in hot_pool[:2]]

    dynamic_candidates = [n for n in flat if n not in hot]
    dynamic_freq = Counter(dynamic_candidates)
    dynamic_sorted = sorted(dynamic_freq.items(), key=lambda x: (-x[1], -dynamic_candidates[::-1].index(x[0])))[:3]
    dynamic = [n for n, _ in dynamic_sorted[:2]]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra = pool[:3]

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
