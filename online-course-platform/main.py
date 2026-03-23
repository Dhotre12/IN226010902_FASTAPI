from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import math

app = FastAPI(title="LearnHub Online Courses")

# ==========================================
# DATA STORES (Q2, Q4, Q14)
# ==========================================
courses = [
    {"id": 1, "title": "Full Stack Web Dev", "instructor": "Alice", "category": "Web Dev", "level": "Beginner", "price": 4000, "seats_left": 10},
    {"id": 2, "title": "Data Science Bootcamp", "instructor": "Bob", "category": "Data Science", "level": "Intermediate", "price": 5000, "seats_left": 4},
    {"id": 3, "title": "UI/UX Masterclass", "instructor": "Charlie", "category": "Design", "level": "Beginner", "price": 3000, "seats_left": 20},
    {"id": 4, "title": "Advanced DevOps", "instructor": "Dave", "category": "DevOps", "level": "Advanced", "price": 6000, "seats_left": 2},
    {"id": 5, "title": "React for Beginners", "instructor": "Alice", "category": "Web Dev", "level": "Beginner", "price": 2000, "seats_left": 15},
    {"id": 6, "title": "Intro to Git", "instructor": "Dave", "category": "DevOps", "level": "Beginner", "price": 0, "seats_left": 50},
]

enrollments = []
enrollment_counter = 1

wishlist = []

# ==========================================
# PYDANTIC MODELS (Q6, Q9, Q11, Q15)
# ==========================================
class EnrollRequest(BaseModel):
    student_name: str = Field(..., min_length=2)
    course_id: int = Field(..., gt=0)
    email: str = Field(..., min_length=5)
    payment_method: str = "card"
    coupon_code: str = ""
    gift_enrollment: bool = False
    recipient_name: str = ""

    @model_validator(mode='after')
    def check_gift_recipient(self):
        if self.gift_enrollment and not self.recipient_name:
            raise ValueError("recipient_name is required if gift_enrollment is True")
        return self

class NewCourse(BaseModel):
    title: str = Field(..., min_length=2)
    instructor: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    level: str = Field(..., min_length=2)
    price: int = Field(..., ge=0)
    seats_left: int = Field(..., gt=0)

class EnrollAllRequest(BaseModel):
    student_name: str
    payment_method: str = "card"

# ==========================================
# HELPER FUNCTIONS (Q7, Q10)
# ==========================================
def find_course(course_id: int):
    for c in courses:
        if c["id"] == course_id:
            return c
    return None

def calculate_enrollment_fee(price: int, seats_left: int, coupon_code: str) -> float:
    discounted_price = float(price)
    
    # 10% early-bird discount if more than 5 seats are left
    if seats_left > 5:
        discounted_price *= 0.90
        
    # Apply coupon codes
    if coupon_code == "STUDENT20":
        discounted_price *= 0.80
    elif coupon_code == "FLAT500":
        discounted_price -= 500
        
    return max(0.0, discounted_price)

def filter_courses_logic(category: str, level: str, max_price: int, has_seats: bool):
    filtered = courses
    if category is not None:
        filtered = [c for c in filtered if c["category"].lower() == category.lower()]
    if level is not None:
        filtered = [c for c in filtered if c["level"].lower() == level.lower()]
    if max_price is not None:
        filtered = [c for c in filtered if c["price"] <= max_price]
    if has_seats is not None:
        if has_seats:
            filtered = [c for c in filtered if c["seats_left"] > 0]
        else:
            filtered = [c for c in filtered if c["seats_left"] == 0]
    return filtered

# ==========================================
# ROUTE ORDERING: FIXED ROUTES FIRST
# ==========================================

# Q1: Home Route
@app.get("/")
def home():
    return {"message": "Welcome to LearnHub Online Courses"}

# Q2: Get all courses
@app.get("/courses")
def get_all_courses():
    total_seats = sum(c["seats_left"] for c in courses)
    return {
        "total": len(courses),
        "total_seats_available": total_seats,
        "courses": courses
    }

# Q5: Courses Summary
@app.get("/courses/summary")
def get_courses_summary():
    free_courses = sum(1 for c in courses if c["price"] == 0)
    most_expensive = max(courses, key=lambda x: x["price"]) if courses else None
    total_seats = sum(c["seats_left"] for c in courses)
    
    categories = {}
    for c in courses:
        categories[c["category"]] = categories.get(c["category"], 0) + 1

    return {
        "total_courses": len(courses),
        "free_courses_count": free_courses,
        "most_expensive_course": most_expensive,
        "total_seats_across_all": total_seats,
        "category_breakdown": categories
    }

# Q10: Filter Courses
@app.get("/courses/filter")
def filter_courses(
    category: Optional[str] = None, 
    level: Optional[str] = None, 
    max_price: Optional[int] = None, 
    has_seats: Optional[bool] = None
):
    results = filter_courses_logic(category, level, max_price, has_seats)
    return {"total_found": len(results), "results": results}

# Q16: Search Courses
@app.get("/courses/search")
def search_courses(keyword: str = Query(..., min_length=1)):
    keyword = keyword.lower()
    matches = [
        c for c in courses 
        if keyword in c["title"].lower() 
        or keyword in c["instructor"].lower() 
        or keyword in c["category"].lower()
    ]
    if not matches:
        return {"message": f"No courses found matching '{keyword}'."}
    return {"total_found": len(matches), "results": matches}

# Q17: Sort Courses
@app.get("/courses/sort")
def sort_courses(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "title", "seats_left"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by field")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Order must be 'asc' or 'desc'")
        
    reverse = order == "desc"
    sorted_courses = sorted(courses, key=lambda x: x[sort_by], reverse=reverse)
    return {"sort_by": sort_by, "order": order, "results": sorted_courses}

# Q18: Paginate Courses
@app.get("/courses/page")
def paginate_courses(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(courses) / limit)
    
    return {
        "total": len(courses),
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "results": courses[start:end]
    }

# Q20: Browse Courses (Combined)
@app.get("/courses/browse")
def browse_courses(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    max_price: Optional[int] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    # 1. Filter
    filtered = filter_courses_logic(category, level, max_price, None)
    
    # 2. Search
    if keyword:
        keyword = keyword.lower()
        filtered = [
            c for c in filtered 
            if keyword in c["title"].lower() 
            or keyword in c["instructor"].lower() 
            or keyword in c["category"].lower()
        ]
        
    # 3. Sort
    if sort_by in ["price", "title", "seats_left"]:
        reverse = order == "desc"
        filtered = sorted(filtered, key=lambda x: x[sort_by], reverse=reverse)

    # 4. Paginate
    total = len(filtered)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    sliced_results = filtered[start:start+limit]

    return {
        "metadata": {
            "keyword": keyword,
            "category": category,
            "level": level,
            "sort_by": sort_by,
            "order": order,
            "page": page,
            "limit": limit,
            "total_matches": total,
            "total_pages": total_pages
        },
        "results": sliced_results
    }

# Q4: Get all enrollments
@app.get("/enrollments")
def get_enrollments():
    return {"total": len(enrollments), "enrollments": enrollments}

# Q19: Search, Sort, Page Enrollments
@app.get("/enrollments/search")
def search_enrollments(student_name: str = Query(..., min_length=1)):
    matches = [e for e in enrollments if student_name.lower() in e["student_name"].lower()]
    return {"total_found": len(matches), "results": matches}

@app.get("/enrollments/sort")
def sort_enrollments(sort_by: str = "final_fee", order: str = "asc"):
    if sort_by not in ["final_fee"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    reverse = (order == "desc")
    sorted_enr = sorted(enrollments, key=lambda x: x[sort_by], reverse=reverse)
    return {"results": sorted_enr}

@app.get("/enrollments/page")
def paginate_enrollments(page: int = 1, limit: int = 5):
    start = (page - 1) * limit
    return {
        "total": len(enrollments),
        "page": page,
        "results": enrollments[start:start+limit]
    }

# Q14: Wishlist System - GET
@app.get("/wishlist")
def get_wishlist():
    total_value = sum(item["price"] for item in wishlist)
    return {"total_items": len(wishlist), "total_value": total_value, "wishlist": wishlist}

# Q14: Wishlist System - POST Add
@app.post("/wishlist/add")
def add_to_wishlist(student_name: str, course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    for item in wishlist:
        if item["student_name"] == student_name and item["course_id"] == course_id:
            raise HTTPException(status_code=400, detail="Course already in wishlist for this student")
            
    wishlist_item = {
        "student_name": student_name,
        "course_id": course_id,
        "course_title": course["title"],
        "price": course["price"]
    }
    wishlist.append(wishlist_item)
    return {"message": "Added to wishlist", "item": wishlist_item}

# Q15: Wishlist System - DELETE Remove
@app.delete("/wishlist/remove/{course_id}")
def remove_from_wishlist(course_id: int, student_name: str):
    global wishlist
    initial_len = len(wishlist)
    wishlist = [item for item in wishlist if not (item["course_id"] == course_id and item["student_name"] == student_name)]
    if len(wishlist) == initial_len:
        raise HTTPException(status_code=404, detail="Item not found in wishlist")
    return {"message": "Removed from wishlist successfully"}

# Q15: Wishlist System - POST Enroll All
@app.post("/wishlist/enroll-all", status_code=status.HTTP_201_CREATED)
def enroll_all_wishlist(req: EnrollAllRequest):
    global wishlist, enrollment_counter
    student_items = [item for item in wishlist if item["student_name"] == req.student_name]
    
    if not student_items:
        raise HTTPException(status_code=400, detail="Wishlist is empty for this student")
        
    confirmations = []
    grand_total = 0.0
    
    for item in student_items:
        course = find_course(item["course_id"])
        if course and course["seats_left"] > 0:
            final_fee = calculate_enrollment_fee(course["price"], course["seats_left"], "")
            course["seats_left"] -= 1
            
            enrollment = {
                "enrollment_id": enrollment_counter,
                "student_name": req.student_name,
                "course_title": course["title"],
                "final_fee": final_fee,
                "status": "confirmed"
            }
            enrollments.append(enrollment)
            confirmations.append(enrollment)
            grand_total += final_fee
            enrollment_counter += 1

    # Clear student's wishlist
    wishlist = [item for item in wishlist if item["student_name"] != req.student_name]

    return {
        "message": "Bulk enrollment successful",
        "total_enrolled": len(confirmations),
        "grand_total_fee": grand_total,
        "confirmations": confirmations
    }

# ==========================================
# ROUTE ORDERING: VARIABLE ROUTES LAST
# ==========================================

# Q11: Add new course
@app.post("/courses", status_code=status.HTTP_201_CREATED)
def add_course(course: NewCourse):
    for c in courses:
        if c["title"].lower() == course.title.lower():
            raise HTTPException(status_code=400, detail="Course title already exists")
            
    new_id = max(c["id"] for c in courses) + 1 if courses else 1
    new_c = course.model_dump()
    new_c["id"] = new_id
    courses.append(new_c)
    return new_c

# Q8 & Q9: Create Enrollment
@app.post("/enrollments", status_code=status.HTTP_201_CREATED)
def create_enrollment(req: EnrollRequest):
    global enrollment_counter
    course = find_course(req.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if course["seats_left"] <= 0:
        raise HTTPException(status_code=400, detail="No seats left for this course")
        
    final_fee = calculate_enrollment_fee(course["price"], course["seats_left"], req.coupon_code)
    course["seats_left"] -= 1
    
    enrollment = {
        "enrollment_id": enrollment_counter,
        "student_name": req.student_name,
        "course_title": course["title"],
        "instructor": course["instructor"],
        "original_price": course["price"],
        "final_fee": final_fee,
        "gift": req.gift_enrollment,
        "recipient": req.recipient_name,
        "status": "confirmed"
    }
    enrollments.append(enrollment)
    enrollment_counter += 1
    
    return enrollment

# Q3: Get course by ID
@app.get("/courses/{course_id}")
def get_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# Q12: Update course
@app.put("/courses/{course_id}")
def update_course(course_id: int, price: Optional[int] = None, seats_left: Optional[int] = None):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if price is not None:
        course["price"] = price
    if seats_left is not None:
        course["seats_left"] = seats_left
        
    return {"message": "Course updated", "course": course}

# Q13: Delete course
@app.delete("/courses/{course_id}")
def delete_course(course_id: int):
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check if any enrollments reference this course
    for e in enrollments:
        if e["course_title"] == course["title"]:
            raise HTTPException(status_code=400, detail="Cannot delete course with active enrollments")
            
    courses.remove(course)
    return {"message": f"Course '{course['title']}' deleted successfully"}