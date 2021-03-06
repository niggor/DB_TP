from api.tools.entities import users, forums
import time


from api.tools import DBconnect

"""
Helper class to manipulate with thread.
"""


def save_thread(forum, title, isClosed, user, date, message, slug, optional):
    DBconnect.exist(entity="user", identifier="email", value=user)
    DBconnect.exist(entity="forum", identifier="short_name", value=forum)

    isDeleted = 0
    if "isDeleted" in optional:
        isDeleted = optional["isDeleted"]
    thread = DBconnect.select_query(
        'select date, forum, id, isClosed, isDeleted, message, slug, title, user, dislikes, likes, points, posts '
        'FROM thread WHERE slug = %s', (slug, )
    )
    if len(thread) == 0:
        DBconnect.update_query('INSERT INTO thread (forum, title, isClosed, user, date, message, slug, isDeleted) '
                               'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                               (forum, title, isClosed, user, date, message, slug, isDeleted, ))
        thread = DBconnect.select_query(
            'select date, forum, id, isClosed, isDeleted, message, slug, title, user, dislikes, likes, points, posts '
            'FROM thread WHERE slug = %s', (slug, )
        )
    thread = thread[0]
    response = {
        'date': str(thread[0]),
        'forum': thread[1],
        'id': thread[2],
        'isClosed': bool(thread[3]),
        'isDeleted': bool(thread[4]),
        'message': thread[5],
        'slug': thread[6],
        'title': thread[7],
        'user': thread[8],
        'dislikes': thread[9],
        'likes': thread[10],
        'points': thread[11],
        'posts': thread[12],
    }

    # Delete few extra elements
    del response["dislikes"]
    del response["likes"]
    del response["points"]
    del response["posts"]

    return response


def details(id, related):
    thread = DBconnect.select_query(
        '''select date, forum, id, isClosed, isDeleted, message, slug, title, user, dislikes, likes, points, IFNULL(posts.posts, 0) FROM thread LEFT JOIN (SELECT thread, COUNT(*) as posts 
                                   FROM post
                                   WHERE post.isDeleted = FALSE
                                   GROUP BY thread) posts ON posts.thread = thread.id
           WHERE id = %s''', (id, )
    )
    if len(thread) == 0:
        raise Exception('No thread exists with id=' + str(id))
    
    thread = thread[0]
    thread = {
        'date': str(thread[0]),
        'forum': thread[1],
        'id': thread[2],
        'isClosed': bool(thread[3]),
        'isDeleted': bool(thread[4]),
        'message': thread[5],
        'slug': thread[6],
        'title': thread[7],
        'user': thread[8],
        'dislikes': thread[9],
        'likes': thread[10],
        'points': thread[11],
        'posts': thread[12],
    }

    if "user" in related:
        thread["user"] = users.details(thread["user"])
    if "forum" in related:
        thread["forum"] = forums.details(short_name=thread["forum"], related=[])

    return thread


def details_in(in_str):
    query = "SELECT date, forum, id, isClosed, isDeleted, message, slug, title, user, dislikes, likes, points, posts FROM thread" \
            " WHERE id IN (%s);"
    print(query % (in_str, ))
    threads = DBconnect.select_query(query, (in_str, ))
    print(in_str)
    print(threads)
    thread_list = {}
    for thread in threads:
        thread = {
            'date': str(thread[0]),
            'forum': thread[1],
            'id': thread[2],
            'isClosed': bool(thread[3]),
            'isDeleted': bool(thread[4]),
            'message': thread[5],
            'slug': thread[6],
            'title': thread[7],
            'user': thread[8],
            'dislikes': thread[9],
            'likes': thread[10],
            'points': thread[11],
            'posts': thread[12],
        }
        thread_list[int(thread['id'])] = thread
    return thread_list


def vote(id, vote):
    print("entered")
    try:
        # DBconnect.exist(entity="thread", identifier="id", value=id)
        if vote == -1:
            DBconnect.update_query("UPDATE thread SET dislikes=dislikes+1, points=points-1 where id = %s", (id, ))
        else:
            DBconnect.update_query("UPDATE thread SET likes=likes+1, points=points+1  where id = %s", (id, ))
    except Exception as e:
        print(e.message)

    return details(id=id, related=[])


def open_close_thread(id, isClosed):
    DBconnect.exist(entity="thread", identifier="id", value=id)
    DBconnect.update_query("UPDATE thread SET isClosed = %s WHERE id = %s", (isClosed, id, ))

    response = {
        "thread": id
    }

    return response


def update_thread(id, slug, message):
    DBconnect.exist(entity="thread", identifier="id", value=id)
    DBconnect.update_query('UPDATE thread SET slug = %s, message = %s WHERE id = %s', (slug, message, id, ))

    return details(id=id, related=[])


def thread_list(entity, identifier, related, params):
        # DBconnect.exist(entity="user", identifier="email", value=identifier)
    query = "SELECT date, forum, id, isClosed, isDeleted, message, slug, title, user, dislikes, likes, points, posts FROM thread WHERE " + entity + " = %s "
    parameters = [identifier]

    if "since" in params:
        query += " AND date >= %s"
        parameters.append(params["since"])
    if "order" in params:
        query += " ORDER BY date " + params["order"]
    else:
        query += " ORDER BY date DESC "
    if "limit" in params:
        query += " LIMIT " + str(params["limit"])
    print(query.format(parameters))
    begin = int(round(time.time() * 1000))
    thread_ids_tuple = DBconnect.select_query(query=query, params=parameters)
    end = int(round(time.time() * 1000))
    print(end - begin)
    begin = int(round(time.time() * 1000))
    thread_list = []
    for thread in thread_ids_tuple:
        thread = {
            'date': str(thread[0]),
            'forum': thread[1],
            'id': thread[2],
            'isClosed': bool(thread[3]),
            'isDeleted': bool(thread[4]),
            'message': thread[5],
            'slug': thread[6],
            'title': thread[7],
            'user': thread[8],
            'dislikes': thread[9],
            'likes': thread[10],
            'points': thread[11],
            'posts': thread[12],
        }
        if "user" in related:
            thread["user"] = users.details(thread["user"])
        if "forum" in related:
            thread["forum"] = forums.details(short_name=thread["forum"], related=[])
        thread_list.append(thread)
    end = int(round(time.time() * 1000))
    print(end - begin)
    return thread_list


def remove_restore(thread_id, status):
    DBconnect.exist(entity="thread", identifier="id", value=thread_id)
    DBconnect.update_query("UPDATE thread SET isDeleted = %s WHERE id = %s", (status, thread_id, ))
    DBconnect.update_query("UPDATE post SET isDeleted = %s WHERE thread = %s", (status, thread_id, ))
    response = {
        "thread": thread_id
    }
    return response


def inc_posts_count(post):
    thread = DBconnect.select_query("SELECT thread FROM post WHERE id = %s", (post, ))
    DBconnect.update_query("UPDATE thread SET posts = posts + 1 WHERE id = %s", (thread[0][0], ))
    return


def dec_posts_count(post):
    thread = DBconnect.select_query("SELECT thread FROM post WHERE id = %s", (post, ))
    try:
        DBconnect.update_query("UPDATE thread SET posts = posts - 1 WHERE id = %s", (thread[0][0], ))
    except Exception as e:
        print(e.message)
    return
