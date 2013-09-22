nirvana v0.3
==
A quick hack to migrate from Menalto Gallery 3.0.x to a fresh installation of ZenPhoto 1.4.x. 



Requirements
--

- A backup of your Gallery 3 files and database.
- Python 2.7-ish.
- SQLalchemy and the appropriate database driver for Python (mysql-python, oursql, ...)
- A fresh, unpopulated ZenPhoto 1.4.x installation.
- Patience. 
- ZenPhoto and Gallery on a local filesystem. Does not require a running web server or PHP.



Usage
--

- Follow the usual procedures for a fresh ZenPhoto 1.4.x installation.

- Edit the database and filesystem paths in _nirvana.py_.

- Add the line below to your zenphoto.cfg file. (Skip this step and you risk causing ZenPhoto to corrupt all database fields containing Unicode characters.)
 ```
define ('FILESYSTEM_CHARSET', 'UTF-8');
 ```

- Run `nirvana.py migrate`.

- Wait.

**Warning**: Don't access ZenPhoto with a browser or any other user agent during migration. If you do, ZenPhoto will attempt to reconcile the inconsistent filesystem state with the inconsistent database state, and you'll have to start from scratch.




Troubleshooting
--

Failed migration?

1. Re-initialize the ZenPhoto database and ZenPhoto data directory.

2. `nirvana.py migrate-verbose`. nirvana will attempt to print human-readable feedback that should help you pinpoint any Unicode titles that are causing problems.

3. Armed with this information, use the Gallery 3 administration tools, to delete or replace all accents, diacritical marks, ellipses in the offending item filenames, titles, and URLs.

4. Lather, rinse, repeat.



Manifesto
--

Gallery 1.x was fun. I miss those days. I can't believe I put up with Gallery 2.x and 3.x for 9 years.



Limitations
--

- nirvana is not very easy or fun to use. Grab a geeky friend.

- Only works with a fresh, empty ZenPhoto installations.

- Does not build thumbnail caches for you. Your first ZenPhoto accesses are what warm up the cache.  Patience is a virtue.

- Brittle. We're talking directly to the database and filesystem. If there were clean APIs you wouldn't need this kind of crap.

- Only sets album thumbnails only when the source item lives at the root of the album. (i.e., if you have Album X and sub-album Y, album X's album cover thumbnail can't be from album Y.)

- Unicode brittleness. You might need to do a few delete/restore/migrate cycles and some manual massaging before you succeed.  See **Troubleshooting**.

- Does not respect or migrate Gallery 3 permissions.

- Imports all photos/albums regardless of whether they are public, and will set all items to `ZEN_ADMIN_USER` (defined in nirvana.py) and make them visible to anyone.

- Characters like quotation marks are filtered out by ZenPhoto's sanitize_path().

 - If you have any `sanizite_path()`-ed characters in your filenames, you will end up with broken images and albums. Running _nirvana migrate-verbose_ will show you the offending file or album name so you can change them in Gallery 3 before attempting migration again.

- Does not care about Windows servers. Maybe you shouldn't either.

- Written in very naive Python and SQL. Left joins? Tuples? What are those?




Version History
--

v0.3 - 20-Apr-2013 - Many major bugs fixed.

v0.2 - 14-Apr-2013 - Initial public release.


Have a nice day.
DMW - <derek@trideja.com>