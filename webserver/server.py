#!/usr/bin/env python

"""
Columbia's COMS W4111.003 Introduction to Databases 
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.
"""

import os
import json
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://hg2579:2837@35.227.37.35/proj1part2"
typeMap = {"up" : "ASC", "down" : "DESC"}

f = open('static/tables.json',) 
tables_col_map = json.load(f) 
f.close()
#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  context = dict(tables=tables_col_map)
  return render_template("index.html", **context)


@app.route('/pickup_map')
def pickup():
  context = dict(map="pickups")
  return render_template("map.html", **context)

@app.route('/dropoff_map')
def dropoff():
  context = dict(map="dropoffs")
  return render_template("map.html", **context)

@app.route('/delete', methods=['GET','POST'])
def delete():
  deleted = False
  if request.form:
    table = request.form['table']
    whereCols = [list(tables_col_map[table].values())[0]]
    if table == "addresses":
      whereCols.append(list(tables_col_map[table].values())[1])
    whereVals = []
    form = dict(request.form)
    for pk in whereCols:
      whereVals.append(form[pk])
    whereV = ' AND '.join([i + '=\'' + j + '\'' for i, j in zip(whereCols, whereVals)])
    if exists(table, whereV):
      stmt = "DELETE FROM {} WHERE {}".format(table, whereV)
      print("DELETE STATEMENT:", stmt)
      try:
        cursor = g.conn.execute(stmt)
        cursor.close()
        deleted = True
      except Exception as e:
        print(e) 
  context = dict(tables=tables_col_map, deleted=deleted)
  return render_template("delete.html", **context)

def exists(table, whereV):
  try:
    cur = g.conn.execute("SELECT 1 FROM {} WHERE {}".format(table, whereV))
  except:
    return False
  return cur.rowcount > 0

@app.route('/insert', methods=['GET','POST'])
def insert():

  inserted = False
  if request.form:
    table = request.form['table']
    columns = list(request.form.keys())[1:]
    values = list(request.form.values())[1:]
    values = ['\'{0}\''.format(v) for v in values]
    stmt = "INSERT INTO {} ({}) VALUES ({})".format(table, ', '.join(columns), ', '.join(values))
    print("INSERT STATEMENT:", stmt)
    try:
      cursor = g.conn.execute(stmt)
      inserted = True
      cursor.close()
    except Exception as e:
      print(e)   
    
  context = dict(tables=tables_col_map, inserted=inserted)
  return render_template("insert.html", **context)

@app.route('/update', methods=['GET','POST'])
def update():
  updated = False
  if request.form:
    table = request.form['table']
    columns = request.form.getlist('columns[]')
    values = request.form.getlist('values[]')
    whereCols = [list(tables_col_map[table].values())[0]]
    if table == "addresses":
      whereCols.append(list(tables_col_map[table].values())[1])
    whereVals = []
    form = dict(request.form)
    for pk in whereCols:
      whereVals.append(form[pk])
    setV = ', '.join([i + '=\'' + j + '\'' for i, j in zip(columns, values)])
    whereV = ' AND '.join([i + '=\'' + j + '\'' for i, j in zip(whereCols, whereVals)])
    stmt = "UPDATE {} SET {} WHERE {}".format(table, setV, whereV)
    print("UPDATE STATEMENT:", stmt)
    try:
      cursor = g.conn.execute(stmt)
      updated = True
      cursor.close()
    except Exception as e:
      print(e)   
    
  context = dict(tables=tables_col_map, updated=updated)
  return render_template("update.html", **context)

@app.route('/query', methods=['GET','POST'])
def query():
  #TODO: try to use a seperate route for this
  if request.form:
    tables = request.form.getlist('tables[]')
    headings = []
    for t in tables:
      headings += [tables_col_map[t][k] for k in tables_col_map[t]]
    print(headings)
    params = {"projection": projection(), "table": join_table(tables), "search": search(request.form['search_col'], request.form['keyword']), "order":order(request.form['sort_col'], request.form['order']), "paging": paging(request.form['rpp'], request.form['page'])}
    print(tables)
    # sql = "select * from hg2579.%(table)s where %(search_col)s ilike \'%%%(keyword)s%%\' order by %(sort_col)s %(order)s limit %(rpp)s offset %(offset)s"%params
    sql = "select %(projection)s from %(table)s %(search)s %(order)s %(paging)s"%params
    print(sql)
    
    cursor = g.conn.execute(text(sql)) # sqlalchemy.text()
    data = []
    for result in cursor:
      row = []
      for header in headings:
        row.append(result[header])
      data.append(row)  # can also be accessed using result[0]
    cursor.close()

    # find the table len
    total_len = 0
    pre_sql = "select %(projection)s from %(table)s %(search)s"%params
    sql = "select count(*) from (%s) as pre"%pre_sql
    print(sql)
    cursor = g.conn.execute(text(sql))
    for result in cursor:
      total_len = result[0]
    cursor.close()

    total_page = 1 + total_len//int(request.form['rpp'])
    print(total_page)
    context = dict(tables=tables_col_map, headings=headings, data = data, total_len = total_len, total_page=total_page)
    return render_template("query.html", **context)

  context = dict(tables=tables_col_map)
  return render_template("query.html", **context)

def projection():
  #TODO: dummy for now
  return "*"

def join_table(tables):
  # to simplify this process, I have changed the column names so that we can perform natural join on the correct key
  if len(tables)==1:
    return tables[0]
  else:
    join = tables[0]
    for table in tables[1:]:
      join += " natural join " + table
  return join

def search(col, keyword):
  # '%keyword%'
  if keyword == "":
    return ""
  else:
    return "where %s ilike \'%%%s%%\'"%(col, keyword)

def order(col, order):
  order = order.lower()
  if order=="asc" or order=="desc":
    return "order by %s %s"%(col, order)
  else:
    return ""

def paging(rpp, page):
  rpp = int(rpp)
  page = int(page)
  offset = rpp*(page-1)
  return "limit %s offset %s"%(str(rpp), str(offset))

@app.route('/stat', methods=['POST', 'GET'])
def stat():
  if request.form:
    headings = ["base_license_number", "count_trip", "count_vehicle", "count_driver"]
    sql = """with trip_ct as (SELECT b.base_license_number, COUNT(trip_id) AS count_trip
FROM bases b left join trips t on b.base_license_number = t.base_license_number
GROUP BY b.base_license_number),
car_ct as (SELECT b.base_license_number, COUNT(vin) AS count_vehicle, count(driver_name) as count_driver
FROM bases b left join vehicles v on b.base_license_number=v.base_license_number 
left join drivers d on v.driver_license_number=d.driver_license_number
GROUP BY b.base_license_number)
select * from trip_ct natural join car_ct"""

    total_len = 0
    total_page = 1
    ct_sql = "select count(*) from (%s) as pre"%sql
    print(ct_sql)
    cursor = g.conn.execute(text(ct_sql))
    for result in cursor:
      total_len = result[0]
    cursor.close()
    sql += " %s %s %s"%(search("base_license_number", request.form['keyword']), order(request.form['sort_col'], request.form['order']), paging(request.form['rpp'],request.form['page']))
    total_page = 1 + total_len//int(request.form['rpp'])
    print(sql)  
    cursor = g.conn.execute(text(sql)) # sqlalchemy.text()
    data = []
    for result in cursor:
      row = []
      for header in headings:
        row.append(result[header])
      data.append(row)  # can also be accessed using result[0]
    cursor.close()
    context = dict(headings=headings, data = data, total_len = total_len, total_page=total_page)
    return render_template("stat.html", **context)
  context = dict()
  return render_template("stat.html", **context)


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='localhost')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
