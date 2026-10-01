<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المنتجات - Morocco in Paris</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f9;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        form {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        form input, form select, form button {
            padding: 10px;
            font-size: 14px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            outline: none;
        }
        form button {
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            grid-column: span 2;
        }
        form button:hover {
            background-color: #218838;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        table th, table td {
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: center;
            font-size: 14px;
        }
        table th {
            background-color: #343a40;
            color: white;
        }
        table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
        }
        .badge-ordered { background-color: #ffc107; color: #333; }
        .badge-ready { background-color: #28a745; }
        .badge-way { background-color: #17a2b8; }
        .delete-btn {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
        }
        .delete-btn:hover {
            background-color: #c82333;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>إدارة تتبع المنتجات - Morocco in Paris</h2>

    <!-- نموذج الإضافة -->
    <form id="productForm">
        <input type="text" id="productName" placeholder="اسم المنتج" required>
        <input type="text" id="addedBy" placeholder="المسؤول عن التسجيل" required>
        <input type="text" id="missingItems" placeholder="الأمور الناقصة للتقييد">
        <select id="status">
            <option value="طلبناها">طلبناها</option>
            <option value="موال">موال (جاهز)</option>
            <option value="فالطريق">فالطريق</option>
        </select>
        <button type="submit">إضافة المنتج</button>
    </form>

    <!-- جدول العرض -->
    <table>
        <thead>
            <tr>
                <th>اسم المنتج</th>
                <th>سجله (المسؤول)</th>
                <th>الأمور الناقصة</th>
                <th>الحالة</th>
                <th>إجراءات</th>
            </tr>
        </thead>
        <tbody id="productTableBody">
            <!-- سيتم تعبئة البيانات تلقائياً عبر JavaScript -->
        </tbody>
    </table>
</div>

<script>
    // جلب البيانات المخزنة مسبقاً أو بدء مصفوفة فارغة
    let products = JSON.parse(localStorage.getItem('mip_products')) || [];

    const form = document.getElementById('productForm');
    const tableBody = document.getElementById('productTableBody');

    function renderTable() {
        tableBody.innerHTML = '';
        products.forEach((product, index) => {
            let badgeClass = '';
            if (product.status === 'طلبناها') badgeClass = 'badge-ordered';
            else if (product.status === 'موال') badgeClass = 'badge-ready';
            else if (product.status === 'فالطريق') badgeClass = 'badge-way';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.addedBy}</td>
                <td>${product.missingItems || 'لا توجد'}</td>
                <td><span class="badge ${badgeClass}">${product.status}</span></td>
                <td><button class="delete-btn" onclick="deleteProduct(${index})">حذف</button></td>
            `;
            tableBody.appendChild(row);
        });
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const newProduct = {
            name: document.getElementById('productName').value,
            addedBy: document.getElementById('addedBy').value,
            missingItems: document.getElementById('missingItems').value,
            status: document.getElementById('status').value
        };

        products.push(newProduct);
        localStorage.setItem('mip_products', JSON.stringify(products));
        
        form.reset();
        renderTable();
    });

    function deleteProduct(index) {
        products.splice(index, 1);
        localStorage.setItem('mip_products', JSON.stringify(products));
        renderTable();
    }

    // التشغيل الأول لتعبئة الجدول
    renderTable();
</script>

</body>
</html>
