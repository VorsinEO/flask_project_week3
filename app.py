import random
import json
import locale
from flask import Flask, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, Length, ValidationError

def get_teachers_list():
    with open('teachers.json', 'r') as f:
        contents = f.read()
    teachers_list = json.loads(contents)
    return teachers_list

def get_goals_list():
    with open('goals.json', 'r') as f:
        contents = f.read()
    goals_list = json.loads(contents)
    return goals_list

def add_booking(id_tutor, day_of_week, time_str, name, phone):
    with open('booking.json', 'r') as r:
        records = json.load(r)
    records.append({'id_tutor':id_tutor,'day_of_week':day_of_week, \
        'time_str':time_str, 'name':name, 'phone': phone})
    
    with open('booking.json', 'w') as w:
        w.write(json.dumps(records))

def add_request(name, phone, goal, r_time):
    with open('requests.json', 'r') as r:
        records = json.load(r)
    records.append({'name':name,'phone':phone, 'goal':goal, 'r_time':r_time})
    
    with open('requests.json', 'w') as w:
        w.write(json.dumps(records))

dow={'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда','thu': 'Четверг',\
    'fri': 'Пятница','sat': 'Суббота','sun': 'Воскресенье'}

class bookingForm(FlaskForm):
    name = StringField('Имя пользователя', [InputRequired(), \
        Length(min=2,max=30,message="Введите от 2 до 30 символов")])
    phone = TelField('Телефон пользователя',[InputRequired(),\
        Length(min=10,max=16,message="Введите от 10 до 16 символов")])
    hidden_day_of_week = HiddenField('День недели')
    hidden_time_str = HiddenField('Время')
    hidden_tutor_id = HiddenField('Преподаватель')

class requestForm(FlaskForm):
    name = StringField('Имя пользователя', [InputRequired(), \
        Length(min=2,max=30,message="Введите от 2 до 30 символов")])
    phone = TelField('Телефон пользователя',[InputRequired(),\
        Length(min=10,max=16,message="Введите от 10 до 16 символов")])
    goal = RadioField('Какая цель занятий?', choices = [("travel","Для путешествий"),("study","Для школы"),\
        ("work","Для работы"),("relocate","Для переезда")], default='travel')
    time = RadioField('Сколько времени есть?', choices = [("1-2 часа в неделю","1-2 часа в неделю"),("3-5 часов в неделю","3-5 часов в неделю")\
        ,("5-7 часов в неделю","5-7 часов в неделю"),("7-10 часов в неделю","7-10 часов в неделю")], default="1-2 часа в неделю")


app = Flask(__name__)
app.secret_key = "randomstring"

#главная
@app.route('/')
def main():
    goals = get_goals_list()
    #возьмем список преподов
    teachers_list = get_teachers_list()
    # генерируем 6 рандомных ид преподов
    six_id = random.sample ([tutor['id'] for tutor in teachers_list], 6)
    # фильтруем список преподов по six_id
    teachers_list_filter = [tutor for tutor in teachers_list if tutor['id'] in six_id]
   
    output = render_template('index.html', teachers_list_filter=teachers_list_filter, goals_dict=goals)
    return output

#цели
@app.route('/goals/<goal>/')
def get_goal(goal):
    goals=get_goals_list()
    goal_label = goals[goal]

    #возьмем список преподов
    teachers_list = get_teachers_list()

    #отфильтруем их по тем, у кого есть нужная цель
    teachers_list_filter = [tutor for tutor in teachers_list if goal in tutor['goals']]
    
    #отсортируем по рейтингу
    teachers_list_filter_sorted = sorted(teachers_list_filter, key=lambda k: k['rating'],reverse=True) 

    output = render_template('goal.html', goal_label=goal_label, teachers_list_filter_sorted = teachers_list_filter_sorted )
    return output

#профиля учителя 
@app.route('/profiles/<int:id_tutor>/')
def get_tutor(id_tutor):
    teachers_list = get_teachers_list()
    tutor = teachers_list[id_tutor]
    goals = get_goals_list()
    output = render_template('profile.html', tutor = tutor, goals = goals, dow=dow)
    return output

#заявки на подбор
@app.route('/request/', methods=["GET","POST"])
def get_request():
    form = requestForm()
    goals = get_goals_list()

    if form.validate_on_submit():
        #нашел на Stack способ передачи данных после валидации и редиректа
        session['r_name'] = form.name.data
        session['r_phone']= form.phone.data
        session['r_goal'] = goals[form.goal.data]
        session['r_time'] = form.time.data
        
        return redirect(url_for('get_request_done'))

    output = render_template('request.html', form = form)
    return output
   
#форма принятой заявки на подбор
@app.route('/request_done/', methods=["GET","POST"])
def get_request_done():
    name = session.pop('r_name')
    phone = session.pop('r_phone')
    goal = session.pop('r_goal')
    r_time = session.pop('r_time')
    
    #запишем в наш JSON новый подбор
    add_request(name, phone, goal, r_time)    

    output = render_template('request_done.html', name = name, phone = phone, goal = goal,\
        r_time = r_time)
    return output

#формы бронирования 
@app.route('/booking/<int:id_tutor>/<day_of_week>/<time>/', methods=["GET","POST"])
def get_booking(id_tutor, day_of_week, time):
    teachers_list = get_teachers_list()
    tutor = teachers_list[id_tutor]
    dow_label = dow[day_of_week]
    #возвращаем исходный вид строке времени, в ссылке приходит первые два символа времени и с  8 часами приходится разбираться
    if time[1]==':':
        time_str = time + '00'
    else:
        time_str = time + ':00'
    form = bookingForm(hidden_day_of_week=day_of_week, hidden_time_str=time_str, hidden_tutor_id=id_tutor)

    if form.validate_on_submit():
        #нашел на Stack способ передачи данных после валидации и редиректа
        session['b_name'] = form.name.data
        session['b_phone']= form.phone.data
        session['b_dow_label'] = dow[form.hidden_day_of_week.data]
        session['b_time'] = form.hidden_time_str.data
        session['b_id_tutor'] = form.hidden_tutor_id.data
        session['b_day_of_week'] = form.hidden_day_of_week.data
        return redirect(url_for('get_booking_done'))

    output = render_template('booking.html', tutor = tutor, day_of_week = day_of_week,\
         dow_label=dow_label, time_str = time_str, form=form)
    return output
    

#принятая заявка на подбор
@app.route('/booking_done/', methods=["GET","POST"])
def get_booking_done():
    name = session.pop('b_name')
    phone = session.pop('b_phone')
    dow_label = session.pop('b_dow_label')
    time_str = session.pop('b_time')
    id_tutor = session.pop('b_id_tutor')
    day_of_week = session.pop('b_day_of_week')
    
    #запишем в наш JSON новый заказ
    add_booking(id_tutor, day_of_week, time_str, name, phone)    

    output = render_template('booking_done.html', name = name, phone = phone, dow_label = dow_label,\
        time_str = time_str, id_tutor = id_tutor)
    return output


if __name__ == '__main__':
    app.run()
