#!/usr/local/bin/python2.7

import sys, os, shutil, datetime, pprint, pdb, datetime
from sqlalchemy import create_engine, Table, Column, Integer, String,\
		func, MetaData, ForeignKey, select, and_
from pipes import quote


# nirvana 0.3 - by DMW <derek@trideja.com>
# I sure hope you read the README:
#    https://github.com/dmwarren/nirvana 


#           _   _   _                 
#  ___  ___| |_| |_(_)_ __   __ _ ___ 
# / __|/ _ \ __| __| | '_ \ / _` / __|
# \__ \  __/ |_| |_| | | | | (_| \__ \
# |___/\___|\__|\__|_|_| |_|\__, |___/
#                           |___/  
# 
SQLALCHEMY_DEBUG	= False


GAL_DB_ENGINE		= 'mysql'
GAL_DB_USERNAME		= ''
GAL_DB_PASSWORD		= ''
GAL_DB_HOSTNAME		= ''
GAL_DB_NAME			= ''
GAL_TABLE_PREFIX	= ''
GAL_FS_ROOT			= '/your/site/gallery3/var/albums'

ZEN_DB_ENGINE		= ''
ZEN_DB_USERNAME		= ''
ZEN_DB_PASSWORD		= ''
ZEN_DB_HOSTNAME		= ''
ZEN_DB_NAME			= ''
ZEN_TABLE_PREFIX	= ''
ZEN_FS_ROOT			= '/your/site/zenphoto/albums'
ZEN_ADMIN_USERID	= 'your_zenphoto_admin_username'


###############################################################################
#
# no user serviceable parts beyond this point
#
###############################################################################

gal_engine = create_engine(	GAL_DB_ENGINE + '://' + 
	GAL_DB_USERNAME + ':' + \
	GAL_DB_PASSWORD + '@' + 
	GAL_DB_HOSTNAME + '/' +	\
	GAL_DB_NAME + \
	'?charset=utf8&use_unicode=1', \
	echo=SQLALCHEMY_DEBUG )
gal_meta		= MetaData(gal_engine)
gal_tags		= Table(GAL_TABLE_PREFIX + 'tags', 
	gal_meta, autoload=True, autoload_with=gal_engine)
gal_items		= Table(GAL_TABLE_PREFIX + 'items', 
	gal_meta, autoload=True, autoload_with=gal_engine)
gal_comments	= Table(GAL_TABLE_PREFIX + 'comments', 
	gal_meta, autoload=True, autoload_with=gal_engine)
gal_itemstags	= Table(GAL_TABLE_PREFIX + 'items_tags',
	gal_meta, autoload=True, autoload_with=gal_engine)

zen_engine = create_engine(	ZEN_DB_ENGINE + '://' + \
	ZEN_DB_USERNAME + ':' + \
	ZEN_DB_PASSWORD + '@' + \
	ZEN_DB_HOSTNAME + '/' + \
	ZEN_DB_NAME + \
	'?charset=utf8&use_unicode=1', \
	echo=SQLALCHEMY_DEBUG )
zen_meta 		= MetaData(zen_engine)

zen_tags 		= Table(ZEN_TABLE_PREFIX + 'tags', 
	zen_meta, autoload=True, autoload_with=zen_engine)
zen_albums		= Table(ZEN_TABLE_PREFIX + 'albums',
	zen_meta, autoload=True, autoload_with=zen_engine)
zen_images		= Table(ZEN_TABLE_PREFIX + 'images',
	zen_meta, autoload=True, autoload_with=zen_engine)
zen_objtag		= Table(ZEN_TABLE_PREFIX + 'obj_to_tag',
	zen_meta, autoload=True, autoload_with=zen_engine)
zen_comments	= Table(ZEN_TABLE_PREFIX + 'comments',
	zen_meta, autoload=True, autoload_with=zen_engine)


def CheapUnixToSQLTime(unix_timestamp):
	# because SQLAlchemy has this built in
	# but I can't be arsed to figure out how to call it
	return(datetime.datetime.fromtimestamp(\
	int(unix_timestamp)).strftime('%Y-%m-%d %H:%M:%S'))

def DumpAlbumList():
	# return a list of Gallery3 album ID numbers
	album_ids = []
	s = select([gal_items.c.id], and_(
		gal_items.c.type == 'album'
	))
	gal_albums_result = gal_engine.execute(s)
	print('Found %s albums.' % str(gal_albums_result.rowcount) )
	for row in gal_albums_result:
		album_ids.append( row['id'] )
	return(album_ids)
	
def DumpGalItems(album_id):
	# return a list of items inside a Gallery3 album
	found_items = []
	s = select([gal_items.c.id], and_(
		gal_items.c.parent_id == album_id
	))
	gal_items_result = gal_engine.execute(s)
	for row in gal_items_result:
		found_items.append( row['id'] )
	return(found_items)

def DumpGalItemMD(item_id):
	# IN: Gallery3 item table ID number
	# OUT: SQLAlchemy ResultProxy of relevant Gallery3 item metadata
	#
	# name: short (URL) name for albums 
	#		or filename for album items
	# title: longname
	# description: blurb
	# parent_id: parent album ID
	# fspath (special case)	
	s = select([gal_items.c.parent_id, gal_items.c.id,
				gal_items.c.name, gal_items.c.title,
				gal_items.c.description, gal_items.c.view_count,
				gal_items.c.created, gal_items.c.updated,
				gal_items.c.width, gal_items.c.height,
				gal_items.c.album_cover_item_id,],
				and_(gal_items.c.id == item_id))
	gal_item_md_result = gal_engine.execute(s)
	return(gal_item_md_result.fetchone())

def MakeZenAlbum(gal_item_md):
	# IN: SQLAlchemy ResultProxy of Gallery Item metadata
	# OUT: nothing
	
	# Gallery3 root albumID = 1
	# Gallery3 albums in root have a parentID of 1
	#
	# ZenPhoto root albumID == NULL, or doesn't have a parent album ID
	# ZenPhoto albums in root have a parentID of NULL
	if gal_item_md['parent_id'] == 1:	
		zen_album_parent_id = None
	else:
		zen_album_parent_id = gal_item_md['parent_id']	

	# if this is a sub-album, follow the path. recurse until you can't.
	if gal_item_md['parent_id'] > 1:

		# This is my really crappy directory recursion code.
		# Don't look at this. It works, but it's terrible. 
		# I can't even tell you why I have to prepend it with the parent
		# album pathname. It's supposed to be recursive. Why are you
		# still reading this?
		# If I was really smart, I would have abstracted this so I 
		# wouldn't have to repeat this in MakeZenAlbumItem().
		
		zen_album_relpath = DumpGalItemMD(gal_item_md['parent_id'])['name'] \
					+ '/' + gal_item_md['name'] + '/'

		# start with an impossible number; this will be reset shortly
		current_parent_album_id = 9999

		parent_album_md = DumpGalItemMD(gal_item_md['parent_id'])
		final_dir_list = []
		first_path_chunk = ''

		# look at the current object. if it has a parent object,
		#	move another level up.
		while parent_album_md['parent_id'] > 1:
			parent_album_md = DumpGalItemMD(parent_album_md['parent_id'])
			final_dir_list.append(parent_album_md['name'])
				
		# flip the order of the list so we don't end up with
		# /level3/level2/level1/root/
		for x in reversed(final_dir_list):
			first_path_chunk += x + '/'

		zen_album_relpath = first_path_chunk + zen_album_relpath 
		final_dir_fullpath = zen_album_relpath[0:-1]
	else:
		zen_album_relpath = gal_item_md['name']
		final_dir_fullpath = zen_album_relpath


	if migrate_verbose == True:
		print("mkdir -p " + final_dir_fullpath.encode('ascii', 'xmlcharrefreplace'))
	if not os.path.isdir(final_dir_fullpath):
		os.makedirs(final_dir_fullpath)

	if migrate_verbose == True:
		print("ZenPhoto DB: create album ID " + str(gal_item_md['id']) + "\n" + \
		zen_album_relpath.encode('ascii', 'xmlcharrefreplace') + ': ' + \
		gal_item_md['title'].encode('ascii', 'xmlcharrefreplace'))

	zen_engine.execute(zen_albums.insert().values(
		id		 	= gal_item_md['id'],
		parentid	= zen_album_parent_id,
		folder		= final_dir_fullpath,
		title		= gal_item_md['name'],
		desc		= gal_item_md['title'],
		date		= CheapUnixToSQLTime(gal_item_md['created']),
		updateddate	= CheapUnixToSQLTime(gal_item_md['updated']),
		thumb		= DumpGalItemMD(gal_item_md['album_cover_item_id'])['name'],
		sort_type	= None,
		mtime		= gal_item_md['created'],
		hitcounter	= gal_item_md['view_count'],
		codeblock	= 'a:0:{}',
		owner		= ZEN_ADMIN_USERID,
	))
	return


def MakeZenAlbumItem(album_md, gal_item_md):
	# IN: the metadata of this item's parent album,
	#		the metadata for the item itself
	# OUT: nothing

	# if this is a sub-album, prefix this path 
	# with the shortname/URL name of the sub-album

	# if this is a sub-album, follow the path. recurse until you can't.
	if album_md['parent_id'] > 1:
		# This is my really crappy directory recursion code.
		# Don't look at this. It works, but it's terrible. 
		# I can't even tell you why I have to prepend it with the parent
		# album pathname. It's supposed to be recursive. Why are you
		# still reading this?
		# If I was really smart, I would have abstracted this so I 
		# wouldn't have to repeat this in MakeZenAlbum().
		item_relpath = DumpGalItemMD(album_md['parent_id'])['name'] \
		+ '/' + album_md['name'] + '/'

		# start with an impossible number; this will be reset shortly
		current_parent_album_id = 9999

		parent_album_md = DumpGalItemMD(album_md['parent_id'])
		first_path_chunk = ''
		final_dir_list = []
 
		# look at the current object. if it has a parent object,
		#	move another level up.
		while parent_album_md['parent_id'] > 1:
			parent_album_md = DumpGalItemMD(parent_album_md['parent_id'])
			final_dir_list.append(parent_album_md['name'])

		# flip the order of the list so we don't end up with
		# /level3/level2/level1/root/
		for x in reversed(final_dir_list):
			first_path_chunk += x + '/'
		item_relpath = first_path_chunk + item_relpath + gal_item_md['name']
	else:
		item_relpath = album_md['name'] + '/' + gal_item_md['name']

	gal_item_fullpath = GAL_FS_ROOT + '/' + item_relpath.encode('utf-8')
	zen_item_fullpath = ZEN_FS_ROOT + '/' + item_relpath.encode('utf-8')

	if migrate_verbose == True:
		print('* ' + item_relpath.encode('ascii', 'xmlcharrefreplace') + ' : ' +\
			gal_item_md['title'].encode('ascii', 'xmlcharrefreplace'))
	else:
		print(str(gal_item_md['parent_id']) + ":" + str(gal_item_md['id'])),

	# copy files
	if os.path.isdir(gal_item_fullpath) == False:
		shutil.copy2(gal_item_fullpath, zen_item_fullpath)

	zen_engine.execute(zen_images.insert().values(
		id			= gal_item_md['id'],
		albumid		= gal_item_md['parent_id'],
		filename	= gal_item_md['name'],
		title		= gal_item_md['title'],
		desc		= gal_item_md['description'],
		commentson	= 1,
		show		= 1,
		date		= gal_item_md['created'],
		height		= gal_item_md['height'],
		width		= gal_item_md['width'],
		mtime		= gal_item_md['created'],
		publishdate	= gal_item_md['created'],
		hitcounter	= gal_item_md['view_count'],
		codeblock	= None,
		user		= None,
		owner		= ZEN_ADMIN_USERID,
	))	
	return

def migrate_tags():
	print("\n\nCopying tags.")	
	s = select([gal_tags.c.id, gal_tags.c.name,],)
	gal_tags_result = gal_engine.execute(s)
	for row in gal_tags_result:
		zen_engine.execute(zen_tags.insert().values(
			id		= row['id'],
			name	= row['name'],
		))		

	if migrate_verbose == True:
		print(str(row['id']) + ':' + row['name'].encode('ascii', 'xmlcharrefreplace')),
	else:
		print(str(row['id'])),
		
	print("\n\nCopying tag associations.")
	s = select([gal_itemstags.c.id, gal_itemstags.c.item_id, \
		gal_itemstags.c.tag_id,],)
	gal_itemstags_result = gal_engine.execute(s)
	for row in gal_itemstags_result:
		zen_engine.execute(zen_objtag.insert().values(
			id			= row['id'],
			tagid		= row['tag_id'],
			type		= 'images',
			objectid	= row['item_id'],
		))
		print(str(row['item_id']) + ':' + str(row['tag_id'])),
	return

def migrate_comments():
	print("\n\nCopying comments.")	
	s = select([gal_comments.c.id, gal_comments.c.created, 
				gal_comments.c.guest_name, gal_comments.c.item_id,
				gal_comments.c.server_remote_addr, gal_comments.c.text,],)
	gal_comments_result = gal_engine.execute(s)

	for row in gal_comments_result:
		if row['guest_name'] == None:
			final_name = 'nobody'
		else:
			final_name = row['guest_name']
		zen_engine.execute(zen_comments.insert().values(
			name			= final_name,
			ownerid			= row['item_id'],
			date			= CheapUnixToSQLTime(row['created']),
			comment			= row['text'],
			IP				= row['server_remote_addr'],
		))		
		if migrate_verbose == True:
			print(final_name.encode('ascii', 'xmlcharrefreplace') + \
				':' + row['text'].encode('ascii', 'xmlcharrefreplace'))
	return


def Migrate():
	for album in DumpAlbumList():
		cur_album_md = DumpGalItemMD(album)
		# skip the useless-to-us Gallery3 root album record, id #1
		if cur_album_md['id'] > 1:
			if migrate_verbose == True:
				print('Found album ID ' + str(cur_album_md['id']) + \
				': '+ cur_album_md['name'].encode('ascii', 'xmlcharrefreplace'))
			else:
				print('Found album ID ' + str(cur_album_md['id']))
			MakeZenAlbum(cur_album_md)
				
			for item_id in DumpGalItems(album):
				MakeZenAlbumItem(cur_album_md, DumpGalItemMD(item_id))
			print("")	
			print("")	
	migrate_tags()
	migrate_comments()

def Usage():
	print("nirvana - helping you move from Gallery3 to ZenPhoto 1.4.x since 2013\n\
v0.3 - 15-Apr-2013 - a quick hack by Derek <derek@trideja.com>\n\
\n\
Use `less` on this file to view detailed instructions.\n")
	sys.exit(0)
		

def main(argv):
	print("Your current system encoding: " + sys.getdefaultencoding())

	try:
		if sys.argv[1] == 'migrate':
			Migrate()
		elif sys.argv[1] == 'migrate-verbose':
			Migrate()
		else:
			Usage()
			sys.exit(1)

	except IndexError:
		Usage()
		sys.exit(1)

if __name__ == "__main__":
	if sys.argv[1] == 'migrate-verbose':
		migrate_verbose = True
	else:
		migrate_verbose = False
	
	main(sys.argv[1:])
