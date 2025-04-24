import mysql from 'mysql2/promise';

//Modify the connection details to match the details specified while
//deploying the SingleStore workspace:
const HOST = 'svc-3482219c-a389-4079-b18b-d50662524e8a-shared-dml.aws-virginia-6.svc.singlestore.com';
const USER = 'general';
const PASSWORD = 'IrGWs0OsikScMW7FfEOFSizd40N2655s';
const DATABASE = 'datatest1';

// main is run at the end
async function main() {
    let singleStoreConnection;
    try {
        singleStoreConnection = await mysql.createConnection({
        host: HOST,
        user: USER,
        password: PASSWORD,
        database: DATABASE,
        port: 3333
        });
  
        console.log("You have successfully connected to SingleStore.");
    } catch (err) { 
        console.error('ERROR', err);
        process.exit(1);
    } finally {
        if (singleStoreConnection) {
            await singleStoreConnection.end();
        }
    }
}

main();