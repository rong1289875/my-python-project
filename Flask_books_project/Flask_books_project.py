from enum import unique

from IPython.core.release import author
from IPython.lib.deepreload import reload
from flask import Flask, render_template, request, flash, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import backref
from wtforms import SubmitField,StringField
from wtforms.validators import DataRequired

# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

app = Flask(__name__)

#  一.配置数据库
# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3306/flask_books?charset=utf8mb4'
# 是否自动跟踪配置修改
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'sdakfals'

# 创建数据库对象
db = SQLAlchemy(app)

'''
图书馆简单案例：
1.配置数据库
   a.导入SQLAlchemy
   b.创建数据库对象db，并配置数据库参数
   c.终端创建数据库
2.添加图书和作者模型
   a.模型继承db.Model
   b.__tablename__:表名
   c.db.Column:字段
   d.db.relationship:关系引用
3.添加数据
4.使用WTF显示表单
   a.自定义表单类
   b.模板中显示
   c.secret_key / 编码 / csrf_token
5.实现相关的增删逻辑
   a.增减书籍
   b.删除书籍 -->网页中删除-->点击需要发送书籍的ID给删除书籍的路由-->路由需要接受参数
   c.删除作者
'''

#  二.定义作者和书模型
# 定义作者模型
class Author(db.Model):
    # 定义表名
    __tablename__ = 'authors'
    # 定义字段
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(16),unique=True)
    # 关系引用
    # books是给自己(Author模型)用的，author是给Book模型用的
    books = db.relationship('Book',backref='author')

    def __repr__(self):
        # 打印作者姓名
        return 'Author: %s' % self.name
# 定义书模型
class Book(db.Model):
    # 定义表名
    __tablename__ = 'books'
    # 定义字段
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(16),unique=True)
    # 外键(一本书可能有多个作者；一对多) db.ForeignKey('authors.id') 与 authors.id
    author_id = db.Column(db.Integer,db.ForeignKey('authors.id'))

    # 打印书籍的名称和作者id
    def __repr__(self):
        return 'Book: %s' % (self.name, self.author_id)

# 自定义表单类
class AuthorForm(FlaskForm):
    author = StringField('作者',validators=[DataRequired()])
    book = StringField('书籍',validators=[DataRequired()])
    sumbit = SubmitField('提交')

# 删除作者
@app.route('/delete_author/<int:author_id>')
def delete_author(author_id):
    # 1.查询数据库，是否有该ID的书，如果有就删除(先删书，再删作者)，没有就提示错误
    author = Author.query.get(author_id)
    # 如果有就删除(先删书，再删作者)
    if author:
        try:
            # 查询后直接删除
            Book.query.filter_by(author_id=author_id).delete()
            # 删除作者
            db.session.delete(author)
            db.session.commit()
        except Exception as e:
            print(e)
            flash('删除作者错误')
            db.session.rollback()
    return redirect(url_for('index'))

# 删除书籍 -->网页中删除-->点击需要发送书籍的ID给删除书籍的路由-->路由需要接受参数
@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    # 1.查询数据库，是否有该ID的书，如果有就删除，没有就提示错误
    book = Book.query.get(book_id)
    # 2.如果有就删除
    if book:
        try:
            db.session.delete(book)
            db.session.commit()
        except Exception as e:
            print(e)
            flash('删除书籍错误')
            db.session.rollback()
    else:
        # 3.没有提示错误
        flash('书籍找不到')
    # redirect:重定向 需要传入路由网址
    # url_for('index'):需要传入视图函数名，返回视图函数对应的路由地址
    print(url_for('index'))
    return redirect(url_for('index'))

@app.route('/',methods=['GET','POST'])
def index():
    # 创建自定义的表单类
    # form = AuthorForm()
    ''''
    验证逻辑
    1.调用WTF的函数实现验证
    2.验证通过获取数据
    3.判断作者是否存在
    4.如果作者存在，判断书籍是否存在，没有书籍就添加数据，如果重复提示错误
    5.如果作者不存在，添加书籍
    6.验证不通过就提示和错误
    '''
    # 1.调用WTF的函数实现验证
    if form.validate_on_submit():
        # 2.通过验证获取数据
        author_name = form.author.data
        book_name = form.book.data
        # 3.判断作者是否存在
        author = Author.query.filter_by(name=author_name).first()
        # 4.如果作者存在
        if author:
            # 判断书籍是否存在，没有书籍就添加数据，
            book = Book.query.filter_by(name=book_name).first()
            # 如果重复提示错误
            if book:
                flash('以存在同名书籍')
            # 没有书籍就添加数据
            else:
                try:
                    new_book = Book(name=book_name,author_id=author_name.id)
                    db.session.add(new_book)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    flash('添加书籍失败')
                    db.session.rollback()
        else:
            # 5.如果作者不存在，添加作者和书籍
            try:
                new_author = Author(name = author_name)
                db.session.add(new_author)
                db.session.commit()

                new_book = Book(name=book_name,author_id = new_author.id)
                db.session.add(new_book)
                db.session.commit()
            except Exception as e:
                print(e)
                flash('添加作者失败')
                db.session.rollback()
    else:
        # 验证不通过就提示错误
        if request.method == 'post':
            flash('参数不全')


    # 查询所有的作者信息，让信息传递给模板
    authors = Author.query.all()
    return render_template('books.html',authors=authors,form=form)



if __name__ == '__main__':
    # 将数据库操作包裹在应用上下文中

#  三.添加数据
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 生成数据
        au1 = Author(name='李四')
        au2 = Author(name='张三')
        au3 = Author(name='王五')

        # 修正：add_all 参数应为列表
        db.session.add_all([au1, au2, au3])  # 注意这里改成列表
        db.session.commit()

        bk1 = Book(name='python基础', author_id=au1.id)
        bk2 = Book(name='java基础', author_id=au1.id)
        bk3 = Book(name='javascript基础', author_id=au2.id)
        bk4 = Book(name='flask基础', author_id=au3.id)
        bk5 = Book(name='spark基础', author_id=au3.id)

        db.session.add_all([bk1, bk2, bk3, bk4, bk5])  # 保持列表形式
        db.session.commit()

    app.run()
