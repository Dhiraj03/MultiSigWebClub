
import datetime    # For the timestamp
import hashlib     # To use the SHA256 hashing algorithm
import json        # To use JSON files for input 
from flask import Flask, jsonify, request    # To handle the web interface of the blockchain
import requests 
from uuid import uuid4
from urllib.parse import urlparse
#These two functions will be used to give an address and URL to the nodes
#To add nodes to our blockchain network, we will also need the request file

# 1 - Building the blockchain
class Blockchain:
    
    def __init__(self):
        self.chain = []
        #The list of transactions should be added before the create_block function
        #as the transcations will be added in the block as a new key
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()
    # To add a new block when it is mined
    def create_block(self, proof, previous_hash):
        block  = {"index": len(self.chain)+1, 
                  'timestamp': str(datetime.datetime.now()),
                  'proof': proof,
                  'previous_hash' : previous_hash,
                  "transactions": self.transactions
                    }
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    # To find the golden nonce( proof of work)
    def proof_of_work(self, previous_proof):
        new_proof =1
        check_proof = False
        while check_proof is False:
            hash_operation  = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4:] == '0000':
                check_proof = True
            else: 
                new_proof += 1
        return new_proof
    # To hash the block
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    # To check if the chain is valid
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block["previous_hash"]!=self.hash(previous_block):
                return False
            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation =  hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[0:4:]!='0000':
                return False
            previous_block = block
            block_index += 1
        return True
    # To add a transaction to the list of transactions in the mempool
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({"sender":sender,
                                  "receiver":receiver,
                                  "amount":amount
                                  })
        previous_block = self.get_previous_block()
        return previous_block['index']+1
#The add_node function is used to add a node to the set of nodes
#The netloc function gives the URL, including the port
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
#The replace_chain function will be called in individual nodes to check for the longest
#blockchain, and if the node's chain is shorter, it is replaced with the longer one
    def replace_chain(self):
        network = self.nodes
        longest_chain = None 
        max_length = len(self.chain) #Length of the chain we are currently dealing with
        for node in network:
            response = requests.get(f"https://{node}/get_chain")  # To get the specific node's blockchain
            if response.status_code == 200: #To check if the request was a success
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

 
#Creating a web app
app = Flask(__name__)

#Creating an address for the node on port 5000
node_address = str(uuid4()).replace('-','')
    
blockchain = Blockchain()


#Mining a new block  - The transactions need to be added here
@app.route('/mine_block', methods=['GET'])
def mine_block():
        previous_block =  blockchain.get_previous_block()
        previous_proof = previous_block["proof"]
        proof = blockchain.proof_of_work(previous_proof)
        previous_hash = blockchain.hash(previous_block)
        #Mining reward is given below, sender is the 5000 node and I'm the miner
        blockchain.add_transaction(sender=node_address, receiver='<Miner>', amount = 1)
        block = blockchain.create_block(proof,previous_hash)
        response = {'message':"Congratulations, you just mined a block!",
                    "index":block["index"],
                    "timestamp":block["timestamp"],
                    'proof':block['proof'],
                    'previous_hash':block['previous_hash'],
                     'transactions':block['transactions']
                    }
        return jsonify(response), 200
    
#Getting the full blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response =  {'chain':blockchain.chain,
                 'length':len(blockchain.chain)}
    return jsonify(response), 200
# To check of the blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {"message":"All good. The blockchain is valid."}
    else:
        response = {"message":"Sorry, the blockchain is invalid"}
    return jsonify(response), 200

#Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():                                         
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    # To check if the json file contains all the three fields
    if not all (key in json for key in transaction_keys): 
        return "We have an avengers-level problem", 400 
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {"message": f'This transaction will be added to Block {index}' }
    return jsonify(response), 201

#Part 3- Decentralizing our Blockchain

#Connecting new nodes
@app.route('/connect_node', methods=['POST'])               
def connect_node():                                     //  To connect diferent nodes to each other
    json =  request.get_json()
    nodes = json.get('node')
    if nodes is None:
        return "No nodes", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {"message": "All the nodes are now connected. The BatCoin blockchain now contains the following nodes. ",
                 "total_nodes": list(blockchain.nodes)}
    return jsonify(response), 200 
#
@app.route('/replace_chain', methods=['GET'])                  
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {"message":"The nodes had different chains, so the chain was replaced",
                    "new_chain": blockchain.chain }
    else:
        response = {"message":"All good, the chain is the largest one",
                    "replaced_chain":blockchain.chain}
    return jsonify(response), 200

#Running the app
app.run(host = '0.0.0.0', port= 5000)   # To run this on a simulated network of multiple nodes, the port numbers should be changed to 5001,5002,..



    
    
    
        
        
        


