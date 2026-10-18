def sidebar_menu(request):
    if not request.user.is_authenticated:
        return {"sidebar_links": []}

    admin_links = [
        ("Dashboard", "/dashboard/"),
        ("Students", "/students/"),
        ("Academics", "/academics/"),
        ("Attendance", "/attendance/"),
        ("Grades & Results", "/gradebook/"),
        ("Course Registration", "/registration/"),
        ("Fees & Payments", "/fees/"),
        ("Documents", "/documents/"),
        ("Announcements", "/notifications/"),
        ("Help Desk", "/helpdesk/"),
        ("Reports", "/reports/"),
        ("Audit Logs", "/audits/"),
    ]

    student_links = [
        ("Dashboard", "/dashboard/"),
        ("My Profile", "/students/me/"),
        ("Academic Information", "/students/me/"),
        ("Attendance", "/attendance/"),
        ("Grades & Results", "/gradebook/my-results/"),
        ("Course Registration", "/registration/"),
        ("Fees & Payments", "/fees/"),
        ("Documents", "/documents/"),
        ("Notifications", "/notifications/"),
        ("Help Desk", "/helpdesk/"),
        ("Security", "/accounts/password_change/"),
    ]

    is_admin = request.user.is_staff or getattr(request.user, "role", "") == "admin"
    return {"sidebar_links": admin_links if is_admin else student_links}
