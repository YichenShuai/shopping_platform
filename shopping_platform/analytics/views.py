from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order, OrderItem
from products.models import Product
from django.db.models import Sum
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import datetime
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
import base64
import csv
from django.utils.text import slugify

@login_required
def statistics(request):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can view statistics')
        return redirect('product_list')

    # Get time frame and chart type parameters
    if request.method == 'POST':
        time_range = request.POST.get('time_range', 'all')
        chart_type = request.POST.get('chart_type', 'line')
        export_type = request.POST.get('export')
        chart_image_data = request.POST.get('chart_image', '')
    else:
        time_range = request.GET.get('time_range', 'all')
        chart_type = request.GET.get('chart_type', 'line')
        export_type = request.GET.get('export')
        chart_image_data = request.GET.get('chart_image', '')

    today = datetime.date.today()

    # Filter orders by time range
    if time_range == 'day':
        orders = Order.objects.filter(payment_status='Paid', created_at__date=today)
    elif time_range == 'week':
        start_of_week = today - datetime.timedelta(days=today.weekday())
        orders = Order.objects.filter(payment_status='Paid', created_at__date__gte=start_of_week)
    elif time_range == 'month':
        start_of_month = today.replace(day=1)
        orders = Order.objects.filter(payment_status='Paid', created_at__date__gte=start_of_month)
    elif time_range == 'year':
        start_of_year = today.replace(month=1, day=1)
        orders = Order.objects.filter(payment_status='Paid', created_at__date__gte=start_of_year)
    else:  # all
        orders = Order.objects.filter(payment_status='Paid')

    # Calculate statistics
    total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    order_count = orders.count()

    # Sales trends by time period
    if time_range == 'day':
        sales_trend = orders.annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('total_amount')).order_by('date')
    elif time_range == 'week':
        sales_trend = orders.annotate(week=TruncWeek('created_at')).values('week').annotate(total=Sum('total_amount')).order_by('week')
    elif time_range == 'month':
        sales_trend = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('total_amount')).order_by('month')
    elif time_range == 'year':
        sales_trend = orders.annotate(year=TruncYear('created_at')).values('year').annotate(total=Sum('total_amount')).order_by('year')
    else:
        sales_trend = orders.annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('total_amount')).order_by('date')

    # Prepare chart data
    key_map = {
        'day': 'date',
        'week': 'week',
        'month': 'month',
        'year': 'year',
        'all': 'date'
    }
    key = key_map.get(time_range, 'date')
    labels = [str(item[key]) for item in sales_trend if item[key] is not None]
    data = [float(item['total'] or 0) for item in sales_trend if item[key] is not None]

    # Hot Items
    top_products = Product.objects.annotate(total_sold=Sum('order_items__quantity')).order_by('-total_sold')[:5]

    context = {
        'total_sales': total_sales,
        'order_count': order_count,
        'top_products': top_products,
        'labels': labels,
        'data': data,
        'time_range': time_range,
        'chart_type': chart_type,
    }

    # Processing export requests
    if export_type == 'pdf':
        return generate_pdf_report(total_sales, order_count, top_products, labels, data, time_range, chart_image_data)
    elif export_type == 'csv':
        return generate_csv_report(total_sales, order_count, top_products, sales_trend)

    return render(request, 'analytics/statistics.html', context)


def generate_pdf_report(total_sales, order_count, top_products, labels, data, time_range, chart_image_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Sales Statistics Report", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Add a time range
    elements.append(Paragraph(f"Time Range: {time_range.capitalize()}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Add total sales and order quantities
    data_table = [
        ['Metric', 'Value'],
        ['Total Sales', f"${total_sales:.2f}"],
        ['Total Orders', str(order_count)],
    ]
    table = Table(data_table)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
    ])
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Add popular products
    if top_products:
        products_table = [['Product', 'Total Sold']]
        for product in top_products:
            products_table.append([product.name, str(product.total_sold or 0)])
        table = Table(products_table)
        table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
        ])
        elements.append(Paragraph("Top 5 Popular Products", styles['Heading2']))
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Adding a Chart Image
    if chart_image_data:
        try:
            chart_image_data = chart_image_data.split(',')[1]
            image_data = base64.b64decode(chart_image_data)
            image_buffer = BytesIO(image_data)
            elements.append(Paragraph("Sales Trend Chart", styles['Heading2']))
            elements.append(Image(image_buffer, width=400, height=200))
            elements.append(Spacer(1, 12))
        except Exception as e:
            elements.append(Paragraph(f"Error including chart: {str(e)}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_statistics.pdf"'
    return response

def generate_csv_report(total_sales, order_count, top_products, sales_trend):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_statistics.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sales Statistics Report'])
    writer.writerow([''])

    # Total sales and order quantity
    writer.writerow(['Total Sales', f"${total_sales:.2f}"])
    writer.writerow(['Total Orders', order_count])
    writer.writerow([''])

    # Sales Trends
    writer.writerow(['Sales Trend'])
    writer.writerow(['Date', 'Total Sales'])
    for item in sales_trend:
        date = item.get('date') or item.get('week') or item.get('month') or item.get('year')
        writer.writerow([str(date), f"${item['total']:.2f}"])
    writer.writerow([''])

    # Hot Items
    writer.writerow(['Top 5 Popular Products'])
    writer.writerow(['Product', 'Total Sold'])
    for product in top_products:
        writer.writerow([product.name, product.total_sold or 0])

    return response