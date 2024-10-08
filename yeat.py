from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Product Search</title>
</head>
<body>
    <h1>Search for a Product</h1>
    <form action="/search" method="post">
        <label for="product_id">Enter Product ID:</label>
        <input type="text" id="product_id" name="product_id" required>
        <button type="submit">Search</button>
    </form>
    {% if product_info %}
    <h2>Product Information:</h2>
    <ul>
        {% for key, value in product_info.items() %}
        <li>{{ key }}: {{ value }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_FORM)

@app.route('/search', methods=['POST'])
def search():
    product_id = request.form['product_id']
    url = f"http://example.com/api/products/{product_id}"
    response = requests.get(url)
    if response.status_code == 200:
        product_info = response.json()
        return render_template_string(HTML_FORM, product_info=product_info)
    else:
        return render_template_string(HTML_FORM, product_info={"error": "Product not found or API error."})

if __name__ == '__main__':
    app.run(debug=True)
