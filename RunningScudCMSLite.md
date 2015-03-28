The lite app is designed to be a simple lightweight content management system.

# Usage #

Upload the lite directory to Google App Engine, or run it locally. Initially, there will be no content on the website, to add or edit content, visit the `/content_manager` . The content\_manager page is admin only, so you will be prompted to log in with the the admin account.

## Adding a new page ##

To add a new page, visit `/content_manager` and specify the path where the content should be served from. For example, to set the main page which users will see when they visit your\_app.appspot.com, set the path to `/`

## Editing a page ##

To edit an existing page, append the desired path to the content manager page. For example, to edit the main page (`/`) visit `/content_manager/`. To edit a page named `/example.html`, visit `/content_manager/example.html`