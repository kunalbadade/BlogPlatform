CREATE TABLE Blog_Database.users(
user_id INTEGER PRIMARY KEY,
user_name TEXT NOT NULL,
password TEXT NOT NULL,
active_status INTEGER NOT NULL);


CREATE TABLE Blog_Database.articles(
   article_id INTEGER PRIMARY KEY,
   article_title TEXT NOT NULL,
   article_content TEXT NOT NULL,
   user_id INTEGER NOT NULL,   
   createstamp TIMESTAMP,
   updatestamp TIMESTAMP,
   url TEXT NOT NULL,
   FOREIGN KEY(user_id) REFERENCES Users(user_id)
  );

CREATE TABLE Blog_Database.comments(
   comment_id INTEGER NOT NULL PRIMARY KEY, 
   comment_content TEXT ,
   article_id INTEGER NOT NULL,
   user_name TEXT NOT NULL,
   createstamp TIMESTAMP,
   updatestamp TIMESTAMP,
   FOREIGN KEY(user_name) REFERENCES Users(user_name),
   FOREIGN KEY(article_id) REFERENCES articles(article_id),
   CONSTRAINT fk_articles
          FOREIGN KEY (article_id)
          REFERENCES articles(article_id)
          ON DELETE CASCADE
          );

CREATE TABLE Blog_Database.tags(  
	tag_id INTEGER PRIMARY KEY NOT NULL,  
	tag_name TEXT NOT NULL
        );

CREATE TABLE Blog_Database.article_tags(
	article_id INTEGER,
	tag_id INTEGER,
        FOREIGN KEY(article_id) REFERENCES articles(article_id),
        FOREIGN KEY(tag_id) REFERENCES tags(tag_id),
        CONSTRAINT fk_articles
          FOREIGN KEY (article_id)
          REFERENCES articles(article_id)
          ON DELETE CASCADE
        CONSTRAINT fl_tags
          FOREIGN KEY (tag_id)
          REFERENCES tags(tag_id)
          ON DELETE CASCADE 	
);

