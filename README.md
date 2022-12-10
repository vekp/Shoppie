# Shoppie
### Video Demo:  <URL HERE>
### Description:
Shoppie is grocery list web app. It allows users to create multiple lists, each with multiple items. When shopping, items can be crossed off as they are added to your shopping trolley. Lists can be shared among family members, and items can be colour coded to show their priority.

#### Details:
Shoppie is a Python app running the Flask framework to render webpages written in HTML, CSS and Javascript. Bootstrap 5 was utilised for styling. The backend is handled with a SQLite3 database. Shoppie has been deployed on Python Anywhere. 
 
Shoppie was created as the final project in Harvard University's online course CS50x Introduction to Computer Science.

#### Login/Registration:
Visitors to the website will be directed to the login page /login.html if not already logged in. After filling in username and password details, the app checks the username and password hash against those stored in the users table in database.db.  Successfully logging in will redirect to /lists.html.
  
#### Lists:
New users will be required to register on the registration page /register.html, where username, password and password confirmation are entered. If the username is unique and password matches the confirmation, the new user's username and password hash are saved in database.db, then the user is redirected to /lists.html.
  
The main Shopping Lists screen in Shoppie is /lists.html.  It contains a form at the top of the page for entering the name of a new list to add, creating a new row in the lists table of the database.  Below this is a table of the lists that have already been created by the user.  To the right of each list name is the number of items in the list that have not been crossed off, if there are any.  Next to this is an edit button which directs to /edit_list.html.  This is followed by lists that other users have shared with the user.  Again, outstanding number of items is listed, but users do not have access to edit these lists.
  
The /edit_list.html page firstly validates that the list belongs to the current user.  The page contains a form for renaming the list, which updates its row in the lists table.  Below this is another form for sharing the list with another user. Filling this form in will firstly validate that the chosen username is valid and not already shared with, then creates a new row in the shares table of the database to link the sharee to the list. Once a list has shared users, these users are then listed in this page in a table below the forms. A delete button appears next to each user for removing their entry from the shares table.  At the bottom of the page is a delete button, which removes the list from the lists table, any related entries in the shares table, and all entries in the items table.
  
#### Items:
Clicking on a list name will take the user to /items.html.  At the top of this page is the name of the list, and if the list was created by the user, and edit button for the list is displayed.  Below this is a form for adding a new item to the list, which creates a new row in the items table of the database.  Under this is a table all of the items in the chosen list.  Next to each item is the quantity required and an edit button.  Below this is where items that have been crossed off are listed.  Items are coloured according to priority, with the most urgent items in red, followed by orange, yellow and white. Clicking on the name of an item will cross it off or uncross it, and also clears its priority.
  
The /edit_item.html page validates the user's access to edit the item's details, then allows the user to update its entry in the items table by renaming the item, changing the quantity, or setting a required date. This required date determines the item's priority and colour in the shopping list.  There is also a delete button to remove its entry from the items table.
  
#### Instructions:
The /instructions.html page contains a simple guide for users to follow when using Shoppie.

  
