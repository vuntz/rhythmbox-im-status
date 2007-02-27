# coding: utf-8
# vim: set et sw=2:
# 
# Copyright (C) 2007 - Vincent Untz
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
import dbus
from dbus import dbus_bindings

BUS_NAME = 'org.gnome.Gossip'
OBJ_PATH = '/org/gnome/Gossip'
IFACE_NAME = 'org.gnome.Gossip'

class GossipStatusPlugin (rb.Plugin):
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

    entry = sp.get_playing_entry ()
    self.playing_entry_changed (sp, entry)

  def deactivate (self, shell):
    self.shell = None
    sp = shell.get_player ()
    sp.disconnect (self.psc_id)
    sp.disconnect (self.pc_id)
    sp.disconnect (self.pspc_id)

    if self.current_entry is not None:
      self.set_status ("")

  def playing_changed (self, sp, playing):
    self.set_entry (sp.get_playing_entry ())

  def playing_entry_changed (self, sp, entry):
    self.set_entry (entry)

  def playing_song_property_changed (self, sp, uri, property, old, new):
    self.set_status_from_entry ()

  def set_entry (self, entry):
    if entry == self.current_entry:
      return

    self.current_entry = entry

    if entry is None:
      self.set_status ("")
      return

    self.set_status_from_entry ()

  def set_status_from_entry (self):
    db = self.shell.get_property ("db")
    artist = db.entry_get (self.current_entry, rhythmdb.PROP_ARTIST) or _("Unknown")
    song   = db.entry_get (self.current_entry, rhythmdb.PROP_TITLE) or _("Unknown")

    new_status = _(u"♫ %s - %s ♫") % (artist, song)
    self.set_status (new_status)

  def set_status (self, new_status):
    try:
      bus = dbus.SessionBus ()
      gossip_obj = bus.get_object (BUS_NAME, OBJ_PATH)
      gossip = dbus.Interface (gossip_obj, IFACE_NAME)

      state, status = gossip.GetPresence ("")
      gossip.SetPresence (state, new_status)
    except dbus_bindings.DBusException:
      pass
