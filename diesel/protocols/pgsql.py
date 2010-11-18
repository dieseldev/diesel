# XXX: this is NOT a DBAPI client
# if you want one... write an adapter :-P
from diesel import Client, call, receive, ConnectionClosed, send
import struct
import hashlib

PGSQL_PORT = 5432

def log(*args):
	if True:
		print ' '.join(map(str,args))

# TODO: convert more types!
type_functions = {
	1043: str,
	23: int,
}

class PostgresClient(Client):
	def __init__(self, host='localhost', port=PGSQL_PORT, **kw):
		Client.__init__(self, host, port, **kw)
	
	@call
	def connect(self, user='', password='', database=''):
		StartupMessage(user=user, database=database).send()
		response = receive(1)
		msg = MessageTypes[response]()
		msg.receive()
		if msg.authtype == 'md5':
			pmsg = PasswordMessage(user=user, password=password, salt=msg.salt)
			pmsg.send()
			response = receive(1)
			msg = MessageTypes[response]()
			msg.receive()
			if msg.authtype != 'ok':
				raise Exception('Authentication failed')
		for msg in self._fetch_until_ready():
			pass
	
	@call
	def simplequery(self, sqlstring):
		QueryMessage(sqlstring=sqlstring).send()
		return self._recv_results(False)

	@call
	def simplequery_dict(self, sqlstring):
		QueryMessage(sqlstring=sqlstring).send()
		return self._recv_results(True)
	
	@call
	def extquery_prepare(self, sqlstring, name=''):
		ParseMessage(name=name, sqlstring=sqlstring).send()
	
	def _extquery(self, params, name):
		BindMessage(statement_name=name, params=params).send()
		DescribeMessage().send()
		ExecuteMessage().send()
		SyncMessage().send()

	@call
	def extquery(self, params, name=''):
		self._extquery(params, name)
		return self._recv_results(False)

	@call
	def extquery_dict(self, params, name=''):
		self._extquery(params, name)
		return self._recv_results(True)

	def _fetch_until_ready(self):
		while True:
			response = receive(1)
			msg = MessageTypes[response]()
			msg.receive()
			yield msg
			if isinstance(msg, ReadyForQueryMessage):
				break

	def _convert_types(self, cols, row, result_dict):
		if result_dict:
			return dict((c[0], type_functions[c[3]](v)) for c,v in zip(cols, row))
		return tuple(type_functions[c[3]](v) for c,v in zip(cols, row))

	def _recv_results(self, result_dict):
		rows = []
		col_descriptions = None
		for msg in self._fetch_until_ready():
			if isinstance(msg, RowDescriptionMessage):
				col_descriptions = msg.fielddescriptions
			elif isinstance(msg, DataRowMessage):
				rows.append(self._convert_types(col_descriptions, msg.row, result_dict))
		return rows
	
class PostgresMessage(object):
	idbyte = ''
	frontend_only = False
	def __init__(self, **kwargs):
		for k,v in kwargs.iteritems():
			setattr(self, k, v)
	
	def receive(self):
		length, = struct.unpack('!I', receive(4))
		if length > 4:
			allbytes = receive(length-4)
		else:
			allbytes = ''
		self.unpack(allbytes)
	
	def send(self):
		allbytes = self.pack()
		tosend = self.idbyte + struct.pack('!I', len(allbytes)+4) + allbytes
		send(tosend)
	
	def pack(self):
		raise NotImplementedError(type(self))

	def unpack(self, allbytes):
		raise NotImplementedError(type(self))

# AuthenticationOk (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(0)
# Specifies that the authentication was successful.
# 
# AuthenticationKerberosV5 (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(2)
# Specifies that Kerberos V5 authentication is required.
# 
# AuthenticationCleartextPassword (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(3)
# Specifies that a clear-text password is required.
# 
# AuthenticationMD5Password (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(12)
# Length of message contents in bytes, including self.
# 
# Int32(5)
# Specifies that an MD5-encrypted password is required.
# 
# Byte4
# The salt to use when encrypting the password.
# 
# AuthenticationSCMCredential (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(6)
# Specifies that an SCM credentials message is required.
# 
# AuthenticationGSS (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(7)
# Specifies that GSSAPI authentication is required.
# 
# AuthenticationSSPI (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(9)
# Specifies that SSPI authentication is required.
# 
# AuthenticationGSSContinue (B)
# Byte1('R')
# Identifies the message as an authentication request.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int32(8)
# Specifies that this message contains GSSAPI or SSPI data.
# 
# Byten
# GSSAPI or SSPI authentication data.
# 
class AuthenticationMessage(PostgresMessage):
	idbyte = 'R'
	def unpack(self, allbytes):
		authtype, = struct.unpack('!I', allbytes[:4])
		if authtype == 5:
			self.authtype = 'md5'
			self.salt = allbytes[4:]
		elif authtype == 0:
			self.authtype = 'ok'
		else:
			raise Exception('we only support md5, trust, and ident at the moment')
# BackendKeyData (B)
# Byte1('K')
# Identifies the message as cancellation key data. The frontend must save these values if it wishes to be able to issue CancelRequest messages later.
# 
# Int32(12)
# Length of message contents in bytes, including self.
# 
# Int32
# The process ID of this backend.
# 
# Int32
# The secret key of this backend.
# 
class BackendKeyDataMessage(PostgresMessage):
	idbyte = 'K'
	def unpack(self, allbytes):
		log('BackendKeyDataMessage:', allbytes)
# Bind (F)
# Byte1('B')
# Identifies the message as a Bind command.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The name of the destination portal (an empty string selects the unnamed portal).
# 
# String
# The name of the source prepared statement (an empty string selects the unnamed prepared statement).
# 
# Int16
# The number of parameter format codes that follow (denoted C below). This can be zero to indicate that there are no parameters or that the parameters all use the default format (text); or one, in which case the specified format code is applied to all parameters; or it can equal the actual number of parameters.
# 
# Int16[C]
# The parameter format codes. Each must presently be zero (text) or one (binary).
# 
# Int16
# The number of parameter values that follow (possibly zero). This must match the number of parameters needed by the query.
# 
# Next, the following pair of fields appear for each parameter:
# 
# Int32
# The length of the parameter value, in bytes (this count does not include itself). Can be zero. As a special case, -1 indicates a NULL parameter value. No value bytes follow in the NULL case.
# 
# Byten
# The value of the parameter, in the format indicated by the associated format code. n is the above length.
# 
# After the last parameter, the following fields appear:
# 
# Int16
# The number of result-column format codes that follow (denoted R below). This can be zero to indicate that there are no result columns or that the result columns should all use the default format (text); or one, in which case the specified format code is applied to all result columns (if any); or it can equal the actual number of result columns of the query.
# 
# Int16[R]
# The result-column format codes. Each must presently be zero (text) or one (binary).
# 
class BindMessage(PostgresMessage):
	idbyte = 'B'
	def pack(self): # TODO: named destination portal?
		header = struct.pack('!B%ssBHH' % len(self.statement_name), 0, self.statement_name, 0, 0, len(self.params))
		params = ''.join(struct.pack('!I%ss' % len(p), len(p), p) for p in self.params)
		return header + params + struct.pack('!H', 0)
# BindComplete (B)
# Byte1('2')
# Identifies the message as a Bind-complete indicator.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
class BindCompleteMessage(PostgresMessage):
	idbyte = '2'
	def unpack(self, allbytes):
		log('BindCompleteMessage')
# CancelRequest (F)
# Int32(16)
# Length of message contents in bytes, including self.
# 
# Int32(80877102)
# The cancel request code. The value is chosen to contain 1234 in the most significant 16 bits, and 5678 in the least 16 significant bits. (To avoid confusion, this code must not be the same as any protocol version number.)
# 
# Int32
# The process ID of the target backend.
# 
# Int32
# The secret key for the target backend.
# 
# Close (F)
# Byte1('C')
# Identifies the message as a Close command.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Byte1
# 'S' to close a prepared statement; or 'P' to close a portal.
# 
# String
# The name of the prepared statement or portal to close (an empty string selects the unnamed prepared statement or portal).
# 
# CloseComplete (B)
# Byte1('3')
# Identifies the message as a Close-complete indicator.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
# CommandComplete (B)
# Byte1('C')
# Identifies the message as a command-completed response.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The command tag. This is usually a single word that identifies which SQL command was completed.
# 
# For an INSERT command, the tag is INSERT oid rows, where rows is the number of rows inserted. oid is the object ID of the inserted row if rows is 1 and the target table has OIDs; otherwise oid is 0.
# 
# For a DELETE command, the tag is DELETE rows where rows is the number of rows deleted.
# 
# For an UPDATE command, the tag is UPDATE rows where rows is the number of rows updated.
# 
# For a SELECT or CREATE TABLE AS command, the tag is SELECT rows where rows is the number of rows retrieved.
# 
# For a MOVE command, the tag is MOVE rows where rows is the number of rows the cursor's position has been changed by.
# 
# For a FETCH command, the tag is FETCH rows where rows is the number of rows that have been retrieved from the cursor.
# 
# For a COPY command, the tag is COPY rows where rows is the number of rows copied. (Note: the row count appears only in PostgreSQL 8.2 and later.)
# 
class CommandCompleteMessage(PostgresMessage):
	idbyte = 'C'
	def unpack(self, allbytes):
		log('CommandCompleteMessage:', allbytes[:-1])
# CopyData (F & B)
# Byte1('d')
# Identifies the message as COPY data.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Byten
# Data that forms part of a COPY data stream. Messages sent from the backend will always correspond to single data rows, but messages sent by frontends might divide the data stream arbitrarily.
# 
# CopyDone (F & B)
# Byte1('c')
# Identifies the message as a COPY-complete indicator.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
# CopyFail (F)
# Byte1('f')
# Identifies the message as a COPY-failure indicator.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# An error message to report as the cause of failure.
# 
# CopyInResponse (B)
# Byte1('G')
# Identifies the message as a Start Copy In response. The frontend must now send copy-in data (if not prepared to do so, send a CopyFail message).
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int8
# 0 indicates the overall COPY format is textual (rows separated by newlines, columns separated by separator characters, etc). 1 indicates the overall copy format is binary (similar to DataRow format). See COPY for more information.
# 
# Int16
# The number of columns in the data to be copied (denoted N below).
# 
# Int16[N]
# The format codes to be used for each column. Each must presently be zero (text) or one (binary). All must be zero if the overall copy format is textual.
# 
# CopyOutResponse (B)
# Byte1('H')
# Identifies the message as a Start Copy Out response. This message will be followed by copy-out data.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int8
# 0 indicates the overall COPY format is textual (rows separated by newlines, columns separated by separator characters, etc). 1 indicates the overall copy format is binary (similar to DataRow format). See COPY for more information.
# 
# Int16
# The number of columns in the data to be copied (denoted N below).
# 
# Int16[N]
# The format codes to be used for each column. Each must presently be zero (text) or one (binary). All must be zero if the overall copy format is textual.
# 
# DataRow (B)
# Byte1('D')
# Identifies the message as a data row.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int16
# The number of column values that follow (possibly zero).
# 
# Next, the following pair of fields appear for each column:
# 
# Int32
# The length of the column value, in bytes (this count does not include itself). Can be zero. As a special case, -1 indicates a NULL column value. No value bytes follow in the NULL case.
# 
# Byten
# The value of the column, in the format indicated by the associated format code. n is the above length.
# 
class DataRowMessage(PostgresMessage):
	idbyte = 'D'
	def unpack(self, allbytes):
		numcolumns, = struct.unpack('!H', allbytes[:2])
		coldata = allbytes[2:]
		self.row = []
		for x in xrange(numcolumns):
			collen, = struct.unpack('!i', coldata[:4])
			coldata = coldata[4:]
			if collen == -1:
				self.row.append(None)
			else:
				colval, = struct.unpack('!%ss' % collen, coldata[:collen])
				coldata = coldata[collen:]
				self.row.append(colval)
		log('DataRowMessage:', self.row)
# Describe (F)
# Byte1('D')
# Identifies the message as a Describe command.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Byte1
# 'S' to describe a prepared statement; or 'P' to describe a portal.
# 
# String
# The name of the prepared statement or portal to describe (an empty string selects the unnamed prepared statement or portal).
# 
class DescribeMessage(PostgresMessage):
	idbyte = 'D'
	frontend_only = True
	def pack(self):
		return 'P\x00' #TODO: support named portals? (this line assumes the empty string portal)
# EmptyQueryResponse (B)
# Byte1('I')
# Identifies the message as a response to an empty query string. (This substitutes for CommandComplete.)
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
# ErrorResponse (B)
# Byte1('E')
# Identifies the message as an error.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# The message body consists of one or more identified fields, followed by a zero byte as a terminator. Fields can appear in any order. For each field there is the following:
# 
# Byte1
# A code identifying the field type; if zero, this is the message terminator and no string follows. The presently defined field types are listed in Section 46.6. Since more field types might be added in future, frontends should silently ignore fields of unrecognized type.
# 
# String
# The field value.
# 
class ErrorResponseMessage(PostgresMessage):
	idbyte = 'E'
	def unpack(self, allbytes):
		raise Exception(allbytes)
# Execute (F)
# Byte1('E')
# Identifies the message as an Execute command.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The name of the portal to execute (an empty string selects the unnamed portal).
# 
# Int32
# Maximum number of rows to return, if portal contains a query that returns rows (ignored otherwise). Zero denotes "no limit".
# 
class ExecuteMessage(PostgresMessage):
	idbyte = 'E'
	frontend_only = True
	def pack(self):
		return struct.pack('!BI', 0, 0)
# Flush (F)
# Byte1('H')
# Identifies the message as a Flush command.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
class FlushMessage(PostgresMessage):
	idbyte = 'H'
	frontend_only = True
	def pack(self):
		return ''
# FunctionCall (F)
# Byte1('F')
# Identifies the message as a function call.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int32
# Specifies the object ID of the function to call.
# 
# Int16
# The number of argument format codes that follow (denoted C below). This can be zero to indicate that there are no arguments or that the arguments all use the default format (text); or one, in which case the specified format code is applied to all arguments; or it can equal the actual number of arguments.
# 
# Int16[C]
# The argument format codes. Each must presently be zero (text) or one (binary).
# 
# Int16
# Specifies the number of arguments being supplied to the function.
# 
# Next, the following pair of fields appear for each argument:
# 
# Int32
# The length of the argument value, in bytes (this count does not include itself). Can be zero. As a special case, -1 indicates a NULL argument value. No value bytes follow in the NULL case.
# 
# Byten
# The value of the argument, in the format indicated by the associated format code. n is the above length.
# 
# After the last argument, the following field appears:
# 
# Int16
# The format code for the function result. Must presently be zero (text) or one (binary).
# 
# FunctionCallResponse (B)
# Byte1('V')
# Identifies the message as a function call result.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int32
# The length of the function result value, in bytes (this count does not include itself). Can be zero. As a special case, -1 indicates a NULL function result. No value bytes follow in the NULL case.
# 
# Byten
# The value of the function result, in the format indicated by the associated format code. n is the above length.
# 
# NoData (B)
# Byte1('n')
# Identifies the message as a no-data indicator.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
# NoticeResponse (B)
# Byte1('N')
# Identifies the message as a notice.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# The message body consists of one or more identified fields, followed by a zero byte as a terminator. Fields can appear in any order. For each field there is the following:
# 
# Byte1
# A code identifying the field type; if zero, this is the message terminator and no string follows. The presently defined field types are listed in Section 46.6. Since more field types might be added in future, frontends should silently ignore fields of unrecognized type.
# 
# String
# The field value.
# 
class NoticeResponseMessage(PostgresMessage):
	idbyte = 'N'
	def unpack(self, allbytes):
		log('NoticeResponseMessage:', allbytes)
# NotificationResponse (B)
# Byte1('A')
# Identifies the message as a notification response.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int32
# The process ID of the notifying backend process.
# 
# String
# The name of the channel that the notify has been raised on.
# 
# String
# The "payload" string passed from the notifying process.
# 
# ParameterDescription (B)
# Byte1('t')
# Identifies the message as a parameter description.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int16
# The number of parameters used by the statement (can be zero).
# 
# Then, for each parameter, there is the following:
# 
# Int32
# Specifies the object ID of the parameter data type.
# 
# ParameterStatus (B)
# Byte1('S')
# Identifies the message as a run-time parameter status report.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The name of the run-time parameter being reported.
# 
# String
# The current value of the parameter.
# 
class ParameterStatusMessage(PostgresMessage):
	idbyte = 'S'
	def unpack(self, allbytes):
		log('ParameterStatusMessage:', allbytes)
# Parse (F)
# Byte1('P')
# Identifies the message as a Parse command.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The name of the destination prepared statement (an empty string selects the unnamed prepared statement).
# 
# String
# The query string to be parsed.
# 
# Int16
# The number of parameter data types specified (can be zero). Note that this is not an indication of the number of parameters that might appear in the query string, only the number that the frontend wants to prespecify types for.
# 
# Then, for each parameter, there is the following:
# 
# Int32
# Specifies the object ID of the parameter data type. Placing a zero here is equivalent to leaving the type unspecified.
# 
class ParseMessage(PostgresMessage):
	idbyte = 'P'
	def pack(self):
		return struct.pack('!%ssB%ssBH' % (len(self.name), len(self.sqlstring)), self.name, 0, self.sqlstring, 0, 0)
# ParseComplete (B)
# Byte1('1')
# Identifies the message as a Parse-complete indicator.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
class ParseCompleteMessage(PostgresMessage):
	idbyte = '1'
	def unpack(self, allbytes):
		log('ParseCompleteMessage')
# PasswordMessage (F)
# Byte1('p')
# Identifies the message as a password response. Note that this is also used for GSSAPI and SSPI response messages (which is really a design error, since the contained data is not a null-terminated string in that case, but can be arbitrary binary data).
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The password (encrypted, if requested).
# 
class PasswordMessage(PostgresMessage):
	idbyte = 'p'
	def pack(self):
		pword = hashlib.md5()
		pword.update(self.password)
		pword.update(self.user)
		pwordsalt = hashlib.md5()
		pwordsalt.update(pword.hexdigest())
		pwordsalt.update(self.salt)
		return 'md5' + pwordsalt.hexdigest() + '\x00'
# PortalSuspended (B)
# Byte1('s')
# Identifies the message as a portal-suspended indicator. Note this only appears if an Execute message's row-count limit was reached.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
# Query (F)
# Byte1('Q')
# Identifies the message as a simple query.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# String
# The query string itself.
# 
class QueryMessage(PostgresMessage):
	idbyte = 'Q'
	def pack(self):
		return self.sqlstring + '\x00'
# ReadyForQuery (B)
# Byte1('Z')
# Identifies the message type. ReadyForQuery is sent whenever the backend is ready for a new query cycle.
# 
# Int32(5)
# Length of message contents in bytes, including self.
# 
# Byte1
# Current backend transaction status indicator. Possible values are 'I' if idle (not in a transaction block); 'T' if in a transaction block; or 'E' if in a failed transaction block (queries will be rejected until block is ended).
# 
class ReadyForQueryMessage(PostgresMessage):
	idbyte = 'Z'
	def unpack(self, allbytes):
		log('ReadyForQueryMessage, transaction status', allbytes)
# RowDescription (B)
# Byte1('T')
# Identifies the message as a row description.
# 
# Int32
# Length of message contents in bytes, including self.
# 
# Int16
# Specifies the number of fields in a row (can be zero).
# 
# Then, for each field, there is the following:
# 
# String
# The field name.
# 
# Int32
# If the field can be identified as a column of a specific table, the object ID of the table; otherwise zero.
# 
# Int16
# If the field can be identified as a column of a specific table, the attribute number of the column; otherwise zero.
# 
# Int32
# The object ID of the field's data type.
# 
# Int16
# The data type size (see pg_type.typlen). Note that negative values denote variable-width types.
# 
# Int32
# The type modifier (see pg_attribute.atttypmod). The meaning of the modifier is type-specific.
# 
# Int16
# The format code being used for the field. Currently will be zero (text) or one (binary). In a RowDescription returned from the statement variant of Describe, the format code is not yet known and will always be zero.
# 
class RowDescriptionMessage(PostgresMessage):
	idbyte = 'T'
	def unpack(self, allbytes):
		numfields, = struct.unpack('!H', allbytes[:2])
		fields = allbytes[2:]
		self.fielddescriptions = []
		for x in xrange(numfields):
			fieldname, fields = fields.split('\x00', 1)
			table_oid, col_attr, type_oid, type_size, type_modifier, format_code = struct.unpack('!IHIHIH', fields[:18])
			fields = fields[18:]
			self.fielddescriptions.append((fieldname, table_oid, col_attr, type_oid, type_size, type_modifier, format_code))
		log('RowDescriptionMessage:', self.fielddescriptions)
# SSLRequest (F)
# Int32(8)
# Length of message contents in bytes, including self.
# 
# Int32(80877103)
# The SSL request code. The value is chosen to contain 1234 in the most significant 16 bits, and 5679 in the least 16 significant bits. (To avoid confusion, this code must not be the same as any protocol version number.)
# 
# StartupMessage (F)
# Int32
# Length of message contents in bytes, including self.
# 
# Int32(196608)
# The protocol version number. The most significant 16 bits are the major version number (3 for the protocol described here). The least significant 16 bits are the minor version number (0 for the protocol described here).
# 
# The protocol version number is followed by one or more pairs of parameter name and value strings. A zero byte is required as a terminator after the last name/value pair. Parameters can appear in any order. user is required, others are optional. Each parameter is specified as:
# 
# String
# The parameter name. Currently recognized names are:
# 
# user
# The database user name to connect as. Required; there is no default.
# 
# database
# The database to connect to. Defaults to the user name.
# 
# options
# Command-line arguments for the backend. (This is deprecated in favor of setting individual run-time parameters.)
# 
# In addition to the above, any run-time parameter that can be set at backend start time might be listed. Such settings will be applied during backend start (after parsing the command-line options if any). The values will act as session defaults.
# 
# String
# The parameter value.
# 
class StartupMessage(PostgresMessage):
	idbyte = ''
	def pack(self):
		options = ''
		for option in ['user', 'database']: # TODO: support more options
			if hasattr(self, option):
				options += struct.pack('!%ssB%ssB' % (len(option), len(getattr(self, option))), option, 0, getattr(self, option), 0)
		options += struct.pack('!B', 0)
		return struct.pack('!I', 3<<16) + options 
# Sync (F)
# Byte1('S')
# Identifies the message as a Sync command.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 
class SyncMessage(PostgresMessage):
	idbyte = 'S'
	frontend_only = True
	def pack(self):
		return ''
# Terminate (F)
# Byte1('X')
# Identifies the message as a termination.
# 
# Int32(4)
# Length of message contents in bytes, including self.
# 

def is_backend_message(cls):
	try:
		return issubclass(cls, PostgresMessage) and not cls.frontend_only
	except:
		return False

MessageTypes = dict((c.idbyte, c) for k,c in locals().iteritems() if is_backend_message(c))

if __name__ == '__main__':
	from diesel import Application, Loop
	import time

	a = Application()

	def exttest_time():
		db = PostgresClient()
		db.connect(user='user', password='pass', database='test')
		db.extquery_prepare('select userid, fakenum from testtable where groupid=$1 limit 5', 'foobar')
		t = time.time()
		for x in xrange(5000):
			db.extquery(('pgtest',), 'foobar')
		print time.time() - t

	def simpletest_time():
		db = PostgresClient()
		db.connect(user='user', password='pass', database='test')
		t = time.time()
		for x in xrange(5000):
			db.simplequery("select userid, fakenum from testtable where groupid='pgtest' limit 5")
		print time.time() - t

	def pgtest():
		db = PostgresClient()
		db.connect(user='user', password='pass', database='test')
		db.simplequery('select * from testtable limit 2')
		db.simplequery("insert into testtable values ('pgtest', 'pgtest', 5500)")
		db.simplequery("insert into testtable values ('10', 'pgtest', 5500)")
		print db.simplequery("select * from testtable where groupid='10'")
		db.simplequery("update testtable set fakenum=8800 where groupid='pgtest'")
		db.simplequery("select userid, fakenum from testtable where groupid='pgtest' limit 5")
		db.extquery_prepare('select userid, fakenum from testtable where groupid=$1 limit 5', 'foobar')
		print db.extquery(('pgtest',), 'foobar')
		print db.extquery_dict(('pgtest',), 'foobar')
		print db.simplequery("select userid, fakenum from testtable where groupid='pgtest' limit 5")
		print db.simplequery_dict("select userid, fakenum from testtable where groupid='pgtest' limit 5")
	
	a.add_loop(Loop(pgtest))
#	a.add_loop(Loop(exttest_time))
#	a.add_loop(Loop(exttest_time))
#	a.add_loop(Loop(exttest_time))
#	a.add_loop(Loop(exttest_time))
#	a.add_loop(Loop(exttest_time))
#	a.add_loop(Loop(exttest_time))
	a.run()
