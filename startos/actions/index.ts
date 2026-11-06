import { createActions } from '../live/actions'
import { sdk } from '../sdk'
import { config } from './config/config'
import { displaySeed } from './displaySeed'
import { experimental } from './config/experimental'
import { createRune } from './generateRune'
import { revokeRunes } from './revokeRunes'
import { deleteGossipStore } from './deleteGossipStore'
import { resetPassword } from './resetPassword'
import { rescanBlockchain } from './rescanBlockchain'
import { nodeInfo } from './nodeInfo'
import { clearnetVpn } from './clearnetVpn'
import { payInvoice } from './payInvoice'
import { receivePayment } from './receivePayment'

const nodeActions = sdk.Actions.of()
  .addAction(config)
  .addAction(displaySeed)
  .addAction(experimental)
  .addAction(createRune)
  .addAction(revokeRunes)
  .addAction(deleteGossipStore)
  .addAction(resetPassword)
  .addAction(rescanBlockchain)
  .addAction(nodeInfo)
  .addAction(clearnetVpn)
  .addAction(payInvoice)
  .addAction(receivePayment)

export const actions = createActions(undefined, nodeActions)
