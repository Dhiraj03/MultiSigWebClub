pragma solidity ^0.5.1; 

// Smart contract to build a MultiSig wallet

 contract MultiSig
    { 
       
        
        mapping( uint => Transaction) public transactions;    // The mapping acts an array of transactions. individual transactions can be accessed through the transaction ID
        mapping( address => bool) public isOwner;             // This mapping is marked True when the specific user is an isOwner
        mapping ( uint => mapping(address => bool)) public confirmations;  // Returns the status of confirmation of each transaction by each owner    
        
        
        struct Transaction                                   // Each transaction is an instance of the structure 'Transaction', with the amount of ETH,
          {                                                  // the status (to be executed/not), destination address and message as its members
             uint amount;
             address dest;
             bool status;
             bytes data;
          }
          
        address[] public owners;   // Creates an array of owners
        uint count_owners = 0;
        uint required=0;             //  The minimum number of users who need to approve the transaction for it to go through
        uint count_transactions = 0;  // To record the number of transactions 
        
        
        event Deposit(address indexed sender, uint value);                     // Events are used to trigger responses from the interactive environment where we have deployed our contract
        event OwnerAddition( address indexed owner);
        event OwnerRemoval ( address indexed owner);
        event Confirmation(address indexed sender, uint indexed transaction_id);
        event Execution(uint indexed transaction_id);
        event ExecutionFailure(uint indexed transaction_id);
        event Submission(uint indexed transaction_id);


        
        
        
        // The following modifiers are used to check conditions before executing functions, and throw exceptions if an error is encountered
        modifier Admin()   // Used to check if the user ADDING/REMOVING other users is authorised to do so
          { 
               if (msg.sender != address(this))
                   revert();
                _;
          }
          
        modifier OwnerInvalid( address owner)    // To check if the owner is not already present
          { 
               if(isOwner[owner])
                 revert();
                 _;
          }
          
         modifier OwnerExists( address owner)  // To check if the owner exists
          {  
              if(!isOwner[owner])
                 revert();
                 _;
          }
          
          modifier confirmed( uint transaction_id, address owner)   // Inputs a particular transaction ID and owner to check for consensus
         {  if(!confirmations[transaction_id][owner])
               revert();
            _;
         }
         
          modifier not_confirmed(uint transaction_id, address owner) // To check if the particular user hasn't approved the transaction
          { if(confirmations[transaction_id][owner])
                revert();
            _;
          }
         
          modifier transaction_is_valid (address dest)   //  To check if the destination address in the transaction is valid
          {  if(dest==address(0))
               revert();
             _;
          }
          
          modifier notExecuted( uint transaction_id)    //  To check if a transaction has been approved yet
         { 
              if(transactions[transaction_id].status)
                revert();
                _;
         }
         
         
           
          modifier valid_address( address node)  //  To check if the address of the node entered is valid
           { 
              if(node==address(0))
                revert();
            _;
           }
           
          modifier req(uint count)  //  To check if the number of users >0
            { 
                if(count==0)
                  revert();
                _;
            }
           
           
          function() payable external                     // The payable function for the contract which is used to deposit ETH in the wallet
           {
              if(msg.value>0)
                 emit Deposit(msg.sender, msg.value);
           }
           
           
          function InitialList(address[]  memory _owners)  // To enter the inital list of user addresses
            public
            req(_owners.length)
            { 
               for (uint i=0; i<_owners.length; i++) 
               {
                  if (isOwner[_owners[i]] || _owners[i] == address(0))   // To check if the user is not already present 
                   revert();
               isOwner[_owners[i]] = true;
               }
               owners = _owners;
               count_owners = _owners.length;
               required = count_owners/2;
            }
            
            
          function AddOwner( address owner)   // To add a new owner, if not already present in the list
           public
           Admin
           OwnerInvalid(owner)
           valid_address(owner)
           {   isOwner[owner]=true;
               owners.push(owner);
               count_owners+=1;
               required = count_owners/2;
               emit OwnerAddition(owner);
           }
             
          function RemoveOwner( address owner)   // To remove an owner, if present in the list
           public
           Admin
           OwnerExists(owner)
           valid_address(owner)
           {  isOwner[owner]=false;
              for (uint i=0; i<owners.length - 1; i++)
                  if (owners[i] == owner) 
                  {
                     owners[i] = owners[count_owners - 1];
                     break;
                  }
                count_owners-=1;
                required=count_owners/2;
                if(count_owners<0)
                  revert();
                emit OwnerRemoval(owner);
                
            }
                
           function submitTransaction( address destination, uint amount,  bytes memory data )   // For any user to submit a transaction for approval
            public
            OwnerExists(msg.sender)
            returns (uint transaction_id)
            { 
                 transaction_id = addTransaction(destination, amount, data);
                 confirmTransaction(transaction_id, msg.sender);
                 
            }
               
            function confirmTransaction( uint transaction_id, address owner)   // To confirm the event of a particular user confirming a particular transaction
            public
            OwnerExists(owner)
            transaction_is_valid(transactions[transaction_id].dest)
            not_confirmed(transaction_id,owner)
            { confirmations[transaction_id][owner]=true;
              
            }
                 
            function isConfirmed(uint transaction_id)   // To check if the transaction's confirmation has reached consensus
             public
             returns (bool)
             {
                 uint vote = 0;
                 for (uint i=0; i<count_owners; i++)
                 {
                   if (confirmations[transaction_id][owners[i]])   // when the number of approvals is greater than the required number, it executed the transaction
                       vote += 1;
                   if (vote == required)
                      {   
                          executeTransaction(transaction_id);
                          return true;
                          //emit Confirmation(owner, transaction_id);
                      }
                 }
             }      
            
            
            function executeTransaction ( uint transaction_id)
             public
             payable
             notExecuted(transaction_id)
             {
                 
                      Transaction memory tix =  transactions[transaction_id];
                       tix.status = true;
                       address payable destination = address (uint160(tix.dest));
                       destination.transfer(tix.amount);
                           emit Execution(transaction_id);
            
             }
             
             
             
             
             function addTransaction(address destination, uint amount,  bytes memory data)
             internal
             transaction_is_valid(destination)
             returns (uint transaction_id)
             {
                 transaction_id =  count_transactions;
                 transactions[transaction_id]= Transaction({
                     amount:amount,
                     dest:destination,
                     status:false,
                     data:data
                 });
                 count_transactions+=1;
                 emit Submission(transaction_id);
                 
             }
             
             
    }
                 
            
           
           
           
           
           
           
              
        
        
        
               
   
