const assert=require('node:assert/strict'),path=require('node:path');
const m=require(path.resolve(process.argv[2]));
assert.equal(m.manifest.version,'#privkeyio:26.6.10:0');
assert.equal(m.manifest.canMigrateFrom,'=#privkeyio:26.6.10:0 || =26.6.10:0');
assert.equal(m.manifest.canMigrateTo,'=#privkeyio:26.6.10:0');
const original=['config','display-seed','experimental','plugins','watchtower','createrune','revoke-runes','delete-gossip-store','reset-password','watchtower-info','watchtower-client-info','rescan-blockchain','node-info','clearnet-vpn','pay-invoice','receive-payment','clboss-status','clboss-ignore-onchain','clboss-notice-onchain','clboss-unmanage'];
const coordinator=['migrated-admin-init','migrated-review-incoming','migrated-review-outgoing','migrated-grant-confirm','migrated-grant-cancel','migrated-grant-pause','migrated-grant-credential','migrated-grant-status'];
assert.deepEqual(Object.keys(m.actions.actions).sort(),[...original,...coordinator].sort());
console.log('PASS: installed actions preserve 20 official actions and add exactly 8 coordinator actions; exact update boundary');
