from pysteamkit.steam3.cdn_client import CDNClient

class CDNClientPool(object):
	def __init__(self, servers, app_ticket, steamid):
		self.clients = [CDNClient(ip, port, app_ticket, steamid) for (ip, port, load) in servers]
		self.client_pool = []
		
	def get_client(self, depot, app_ticket):
		while len(self.client_pool) > 0:
			client = self.client_pool.pop(0)
			
			if client.depot == depot or (client.app_ticket and client.auth_appticket(depot, app_ticket)) or client.auth_depotid(depot):
				return client
			else:
				if client.mark_failed_request():
					self.client_pool.append(client)
				
		while len(self.clients) > 0:
			client = self.clients.pop(0)
			
			if client.initialize():
				if client.depot == depot or (client.app_ticket and client.auth_appticket(depot, app_ticket)) or client.auth_depotid(depot):
					return client
				else:
					if client.mark_failed_request():
						self.client_pool.append(client)
			else:
				if client.mark_failed_request():
					self.clients.append(client)
				
		raise Exception("Exhausted CDN client pool")
		
	def return_client(self, client):
		self.client_pool.append(client)
