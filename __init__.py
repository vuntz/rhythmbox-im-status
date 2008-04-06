# coding: utf-8
# vim: set et sw=2:
# 
# Copyright (C) 2007-2008 - Vincent Untz
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import rhythmdb, rb
try:
  import dbus
  use_gossip = True
except ImportError:
  use_gossip = False
try:
  import empathy
  use_empathy = True
  empathy_idle = empathy.Idle ()
except ImportError:
  use_empathy = False

BUS_NAME = 'org.gnome.Gossip'
OBJ_PATH = '/org/gnome/Gossip'
IFACE_NAME = 'org.gnome.Gossip'

class IMStatusPlugin (rb.Plugin):
  def __init__ (self):
    rb.Plugin.__init__ (self)

  def activate (self, shell):
    self.shell = shell
    sp = shell.get_player ()
    self.psc_id  = sp.connect ('playing-song-changed',
                               self.playing_entry_changed)
    self.pc_id   = sp.connect ('playing-changed',
                               self.playing_changed)
    self.pspc_id = sp.connect ('playing-song-property-changed',
                               self.playing_song_property_changed)

    self.current_entry = None

    self.save_status ()

    if sp.get_playing ():
      self.set_entry (sp.get_playing_entry ())

  def deactivate (self, shell):
    self.shell = None
    sp = shell.get_player ()
    sp.disconnect (self.psc_id)
    sp.disconnect (self.pc_id)
    sp.disconnect (self.pspc_id)

    if self.current_entry is not None:
      self.restore_status ()

  def playing_changed (self, sp, playing):
    if playing:
      self.set_entry (sp.get_playing_entry ())
    else:
      self.current_entry = None
      self.restore_status ()

  def playing_entry_changed (self, sp, entry):
    if sp.get_playing ():
      self.set_entry (entry)

  def playing_song_property_changed (self, sp, uri, property, old, new):
    if sp.get_playing () and (property == "artist" or property == "title"):
      self.set_status_from_entry ()

  def set_entry (self, entry):
    if entry == self.current_entry:
      return

    if self.current_entry == None:
      self.save_status ()
    self.current_entry = entry

    if entry is None:
      self.restore_status ()
      return

    self.set_status_from_entry ()

  def set_status_from_entry (self):
    db = self.shell.get_property ("db")
    artist = db.entry_get (self.current_entry, rhythmdb.PROP_ARTIST) or _("Unknown")
    song   = db.entry_get (self.current_entry, rhythmdb.PROP_TITLE) or _("Unknown")

    new_status = _(u"♫ %s - %s ♫") % (artist, song)
    self.set_status (new_status)

  def set_status (self, new_status):
    self.set_gossip_status (new_status)
    self.set_empathy_status (new_status)

  def save_status (self):
    self.saved_gossip = self.get_gossip_status ()
    self.saved_empathy = self.get_empathy_status ()

  def restore_status (self):
    if self.saved_gossip != None:
      self.set_gossip_status (self.saved_gossip)
    if self.saved_empathy != None:
      self.set_empathy_status (self.saved_empathy)

  def set_gossip_status (self, new_status):
    if not use_gossip:
      return

    try:
      bus = dbus.SessionBus ()
      gossip_obj = bus.get_object (BUS_NAME, OBJ_PATH)
      gossip = dbus.Interface (gossip_obj, IFACE_NAME)

      state, status = gossip.GetPresence ("")
      gossip.SetPresence (state, new_status)
    except dbus.DBusException:
      pass

  def get_gossip_status (self):
    if not use_gossip:
      return

    try:
      bus = dbus.SessionBus ()
      gossip_obj = bus.get_object (BUS_NAME, OBJ_PATH)
      gossip = dbus.Interface (gossip_obj, IFACE_NAME)

      state, status = gossip.GetPresence ("")
      return status
    except dbus.DBusException:
      return None

  def set_empathy_status (self, new_status):
    if not use_empathy:
      return

    empathy_idle.set_status (new_status)

  def get_empathy_status (self):
    if not use_empathy:
      return

    return empathy_idle.get_status ()
