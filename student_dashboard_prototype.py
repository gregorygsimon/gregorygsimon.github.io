import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import requests, datetime, webbrowser

## This code will not run without MindEdge access / password

if 'un' not in vars():
    un = 'wgudb'
    pw = ''
    if pw=='':
        pw = input("Enter Mindedge password:")

base_url = 'https://wguapps.mindedgeonline.com/services/api/'
domain_id = 55

def get_token(password):
    r = requests.post(base_url+'auth',json = {'username':un,'password':password})
    try:
        return r.json()[0]['token']
    except Exception as e:
        print('status: ',r.status_code,':',r.reason)
        print(e)
        print("Token not returned. Check password is correct")

def get_me_sid(email,token):
    """get MindEdge Student ID"""
    r = requests.post(base_url+'students',
                      json={'token':token,'dId':55,'emailAddress':email})
    return r.json()[0].get('sId')

def get_completion_perc(sid,token):
    """returns dataframe of percent completion by module"""

    r3 = requests.post(base_url+'studentCompleteAssignments',
                       json={'token':token,'dId':55,'cId':612,'sId':sid})

    read_pages = [t['title'] for t in r3.json()] # titles of pages read

    # select only pages with learning content:
    pages = [title for title in read_pages if  (
        '.' in title and
        'Feedback' not in title and
        'Flashcards' not in title and
        'Review' not in title and
        'Problem Set' not in title
    )]

    idx = [i for i in range(1,8)]
    
    # all_pages gives the total possible pages indexed by module
    #   counted manually in Sep 2020
    all_pages = pd.Series([23, 22, 30, 17,  8, 12, 16],index=idx)
    completion=100*pd.Series([int(p[0]) for p in pages])\
                     .value_counts().reindex(idx,fill_value=0)/all_pages
    return completion



def get_quiz_results(sid,token):
    r4 = requests.post(base_url+'studentTestData',
                       json={'token':token,'dId':55,'cId':612,'sId':sid})
    # parsing the text names of the quizzes to give:
    #    the ch number, quiz number, percent, date, and # of questions answered
    data_quiz = [
        (*test['title'].split('Module ')[1].split('Problem Set '),
          result['final_score'],
          result['dateCompleted'],
          result['totalQuestions']
        )
         for test in r4.json() for result in test['resultData']
        ]

    quiz_df = pd.DataFrame(
        data_quiz,
        columns=['Chapter','Problem Set','Percent','Date','Completed']
    )

    quiz_df['Percent'] = pd.to_numeric(quiz_df['Percent'])
    quiz_df['days ago'] = pd.to_datetime(quiz_df['Date'])\
                            .apply(lambda x: (datetime.datetime.now()-x).days)
    quiz_df['# correct'] = quiz_df['Percent']/100 * quiz_df['Completed']
    quiz_df['y_value'] = pd.to_numeric(quiz_df['Chapter'])
    return quiz_df

def get_logins(sid,token):
    """given studentID and active API token,
       returns dataframe of login dates and login duration"""
    r5 = requests.post(base_url+'studentLogins',
                       json={'token':token,'dId':55,'cId':612,'sId':sid})
    studytimes = pd.DataFrame(
        # first 10 characters of 'first_accessed' gives the date
        [(x['first_accessed'][:10],x['duration']/3600) for x in r5.json()]
    )
    studytimes.columns = ['date','duration']
    studytimes = studytimes.groupby('date').sum()

    # to trim outliers/glitches (e.g. 300 hours spent in one session)
    # we make 10 the maximum reported hours possible in one session
    studytimes[studytimes>10] = 10

    studytimes.index = pd.to_datetime(studytimes.index)
    return studytimes


def mindedge_dashboard(sid,token,filename='dashboard.png'):
    """input: studentID, active API token, and image output filename.
       Gathers all student data and creates dashboard locally"""
    studytimes = get_logins(sid,token)
    completion = get_completion_perc(sid,token)
    quiz_df = get_quiz_results(sid,token)

    # reindex studytimes to ensure that at least one month is visible
    # so the min date is the lesser of 1 mo ago and the minimum date in the dataset
    month_ago = (datetime.datetime.now()+datetime.timedelta(days=-30)).date()
    all_dates = pd.date_range(
        min(month_ago, studytimes.index.min()), 
        datetime.datetime.now()
    )
    studytimes_reidx = studytimes.reindex(all_dates,fill_value=0)

    # WGU colors taken from https://www.wgu.edu/about/brand.html
    blue = '#003057'
    lblue = '#4986AD'
    green = '#509E2F'

    # change font
    rcParams['font.sans-serif'] = "Futura Lt BT"
    rcParams['font.family'] = "sans-serif"
    rcParams['font.size'] = 14

    fig, axs = plt.subplots(2, 2, figsize=(12, 8),sharey='row')

    fig.patch.set_facecolor('white')
    plt.subplots_adjust(hspace = 0.3) #more horizontal space between plots

    #top left axis - completion horiz bar chart
    ax = plt.subplot(2,2,1)
    colors = [lblue]*7 
    for i in range(7):
        if completion.iloc[i]==100:
            colors[i]=blue
    plt.barh(completion.index,completion.values,height=1,color=colors,edgecolor='black')
    plt.ylim(0.5,7.5)
    plt.xlim(0,100)
    ax.invert_yaxis()
    ax.set_ylabel('Chapter')
    ax.set_title('Completion of Learning Resource (%)')
    ticks_set = [0,20,40,60,80,100]
    plt.xticks(ticks_set,[str(val)+'%' for val in ticks_set])
    plt.yticks(range(1,8))


    # top right axis - circle plot for quiz results
    ax = plt.subplot(2,2,2);
    sc = plt.scatter(
        quiz_df['Percent'].apply(lambda x: x+np.random.normal(0,0.1)),
        quiz_df['y_value'],
        s=700,alpha=0.8,c=quiz_df['days ago'],cmap=plt.cm.viridis_r,
        vmin=0,vmax=max(14,quiz_df['days ago'].max())
    )
    cbar = plt.colorbar(sc)
    cbar.set_label("Days Since Quiz")
    ax.set_yticks(np.arange(0.5,7.5,1), minor=True)
    plt.ylim(0.5,7.5)
    plt.gca().invert_yaxis() # want Chapter 1 on top, Ch.7 on bottom
    plt.xlim(0,105)
    ax.set_xticks(np.arange(0,105,10))
    ax.tick_params(length=0)
    ax.yaxis.grid(True, which='minor')
    ax.set_ylabel('Chapter')
    ax.set_title('Quiz Results')
    plt.yticks(range(1,8))

    # bottom axis - study times vertical bar chart
    ax = plt.subplot(2,1,2)
    plt.bar(studytimes_reidx.index, studytimes_reidx['duration'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    datemin = studytimes_reidx.index.min()
    datemax = datetime.datetime.today()
    ax.set_xlim(datemin, datemax)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45);
    ax.set_ylabel('hours studied');
    ax.set_title('Hours engaged in Learning Resource');

    plt.savefig(filename,dpi=300,bbox_inches='tight')

    #webbrowser.open('dashboard.png')
