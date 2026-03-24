from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import io
import base64
import seaborn as sns
import time

app = Flask(__name__)

# Function to scrape products from a page with enhanced error handling and debugging
def scrape_products(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        for product in soup.find_all('article', class_='product_pod'):
            name = product.h3.a.text.strip() if product.h3 and product.h3.a else 'N/A'
            price_elem = product.find('p', class_='price_color')
            price = price_elem.text.strip() if price_elem else '£0.00'
            
            # Get product link for description
            link = product.h3.a['href'] if product.h3 and product.h3.a else None
            description = 'No description available'
            if link:
                full_link = f"{base_url}{link}"
                try:
                    prod_response = requests.get(full_link, timeout=10, headers=headers)
                    prod_response.raise_for_status()
                    prod_soup = BeautifulSoup(prod_response.text, 'html.parser')
                    desc_div = prod_soup.find('div', id='product_description')
                    if desc_div and desc_div.p:
                        description = desc_div.p.text.strip()
                    time.sleep(0.1)  # Delay to avoid overwhelming the server
                except Exception as e:
                    print(f"Error fetching description for {name}: {e}")
            
            products.append({'name': name, 'price': price, 'description': description})
        print(f"Scraped {len(products)} products from {url}")  # Debug print
        return products
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# Scrape multiple pages (first 3 pages for demo, as the site has limited pages)
all_products = []
base_url = 'http://books.toscrape.com/'
pages = ['', 'catalogue/page-2.html', 'catalogue/page-3.html']  # Adjust based on site structure
for page in pages:
    url = f'{base_url}{page}'
    all_products.extend(scrape_products(url))

print(f"Total products scraped: {len(all_products)}") 
print("Sample scraped data:", all_products[:3]) 

# Create a custom dataset using pandas
df = pd.DataFrame(all_products)

# Clean price data (remove currency symbol) with enhanced error handling
try:
    df['price'] = df['price'].str.replace('Â£', '').str.strip().astype(float)
    print("Price cleaning successful. Sample prices:", df['price'].head())  # Debug print
except Exception as e:
    print(f"Error cleaning price data: {e}. Defaulting to 0.0")
    df['price'] = 0.0

# Add a dummy category for visualization (since the site doesn't have ratings, we'll simulate based on price)
df['category'] = pd.cut(df['price'], bins=[0, 10, 50, 100, float('inf')], labels=['Low', 'Medium', 'High', 'Premium'])

# Data visualizations
sns.set(style="whitegrid")

try:
    # Visualization 1: Scatter plot of price vs index (since no rating, use index as proxy)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df.reset_index(), x='index', y='price', hue='category', palette='viridis', alpha=0.7)
    plt.title('Product Prices by Index', fontsize=16)
    plt.xlabel('Product Index', fontsize=14)
    plt.ylabel('Price ($)', fontsize=14)
    plt.legend(title='Category')
    plt.tight_layout()
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode()
    plt.close()
except Exception as e:
    print(f"Error creating plot 1: {e}")
    plot_url1 = ''

try:
    # Visualization 2: Histogram of prices
    plt.figure(figsize=(10, 6))
    sns.histplot(df['price'], bins=20, kde=True, color='skyblue')
    plt.title('Distribution of Product Prices', fontsize=16)
    plt.xlabel('Price ($)', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.tight_layout()
    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()
except Exception as e:
    print(f"Error creating plot 2: {e}")
    plot_url2 = ''

try:
    # Visualization 3: Bar chart of category counts
    plt.figure(figsize=(10, 6))
    category_counts = df['category'].value_counts().sort_index()
    sns.barplot(x=category_counts.index, y=category_counts.values)
    plt.title('Count of Products by Category', fontsize=16)
    plt.xlabel('Category', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.tight_layout()
    img3 = io.BytesIO()
    plt.savefig(img3, format='png')
    img3.seek(0)
    plot_url3 = base64.b64encode(img3.getvalue()).decode()
    plt.close()
except Exception as e:
    print(f"Error creating plot 3: {e}")
    plot_url3 = ''

try:
    # Visualization 4: Box plot of prices by category
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='category', y='price')
    plt.title('Price Distribution by Category', fontsize=16)
    plt.xlabel('Category', fontsize=14)
    plt.ylabel('Price ($)', fontsize=14)
    plt.tight_layout()
    img4 = io.BytesIO()
    plt.savefig(img4, format='png')
    img4.seek(0)
    plot_url4 = base64.b64encode(img4.getvalue()).decode()
    plt.close()
except Exception as e:
    print(f"Error creating plot 4: {e}")
    plot_url4 = ''

@app.route('/')
def index():
    # Get sample data (first 10 rows)
    sample_data = df.head(20).to_html(classes='table table-striped table-hover', index=False)
    
    # Summary stats
    summary_stats = df.describe().to_html(classes='table table-striped table-hover')
    
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced Product Dataset Dashboard</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; }
            .jumbotron { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem 1rem; margin-bottom: 2rem; }
            .card { margin-bottom: 2rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            .card-header { background-color: #007bff; color: white; font-weight: bold; }
            img { max-width: 100%; height: auto; border-radius: 8px; }
            .footer { text-align: center; padding: 1rem; background-color: #343a40; color: white; margin-top: 2rem; }
            h1, h2 { color: #495057; }
        </style>
    </head>
    <body>
        <div class="jumbotron text-center">
            <h1 class="display-4"><i class="fas fa-shopping-cart"></i> Web Scaping by Rachit Dataset Dashboard</h1>
            <p class="lead">Scraped from toscrape.com with BeautifulSoup, analyzed with Pandas, and visualized with Matplotlib & Seaborn via Flask.</p>
        </div>
        
        <div class="container">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-info-circle"></i> Dashboard Description
                        </div>
                        <div class="card-body">
                            <p>This dashboard presents a comprehensive analysis of book data scraped from the demo website <a href="http://books.toscrape.com/" target="_blank">books.toscrape.com</a>. It includes product names, prices, descriptions, and categories. The visualizations provide insights into price distributions, category counts, and more. Data is processed using Pandas, and plots are generated with Matplotlib and Seaborn. This is a demo application built with Flask for educational purposes.</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-table"></i> Scraped Data Sample
                        </div>
                        <div class="card-body">
                            <p>Below is a sample of the scraped product data (first 10 rows), including name, price, and description.</p>
                            {{ sample_data|safe }}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-chart-line"></i> Summary Statistics
                        </div>
                        <div class="card-body">
                            <p>Descriptive statistics for the dataset.</p>
                            {{ summary_stats|safe }}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-chart-bar"></i> Visualization 1: Prices by Index
                        </div>
                        <div class="card-body">
                            <p>Scatter plot showing product prices by index.</p>
                            {% if plot_url1 %}
                            <img src="data:image/png;base64,{{ plot_url1 }}" alt="Scatter plot of prices by index">
                            {% else %}
                            <p>Error: Plot could not be generated.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-chart-area"></i> Visualization 2: Price Distribution
                        </div>
                        <div class="card-body">
                            <p>Histogram of product prices with a kernel density estimate.</p>
                            {% if plot_url2 %}
                            <img src="data:image/png;base64,{{ plot_url2 }}" alt="Histogram of prices">
                            {% else %}
                            <p>Error: Plot could not be generated.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-chart-pie"></i> Visualization 3: Category Counts
                        </div>
                        <div class="card-body">
                            <p>Bar chart of the number of products per category.</p>
                            {% if plot_url3 %}
                            <img src="data:image/png;base64,{{ plot_url3 }}" alt="Bar chart of category counts">
                            {% else %}
                            <p>Error: Plot could not be generated.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-box-plot"></i> Visualization 4: Price Box Plot by Category
                        </div>
                        <div class="card-body">
                            <p>Box plot showing price distribution across categories.</p>
                            {% if plot_url4 %}
                            <img src="data:image/png;base64,{{ plot_url4 }}" alt="Box plot of prices by category">
                            {% else %}
                            <p>Error: Plot could not be generated.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer">
            <p>&copy; 2023 Product Dataset Demo. Built with Flask, BeautifulSoup, Pandas, Matplotlib, and Seaborn. <i class="fas fa-heart text-danger"></i></p>
            <p><strong>Note:</strong> This is a demo from toscrape.com. For real Amazon data, use APIs or public datasets. Run with <code>python app.py</code>.</p>
        </footer>
        
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''
    return render_template_string(html_template, sample_data=sample_data, summary_stats=summary_stats, plot_url1=plot_url1, plot_url2=plot_url2, plot_url3=plot_url3, plot_url4=plot_url4)

if __name__ == '__main__':
    app.run(debug=False, port=5000)