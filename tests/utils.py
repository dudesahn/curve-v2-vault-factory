import pytest
import ape, time
from ape import chain, Contract


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def increase_time(chain, seconds):
    chain.pending_timestamp = chain.pending_timestamp + seconds
    chain.mine(timestamp=chain.pending_timestamp)


# returns (profit, loss) of a harvest
def harvest_strategy(
    use_yswaps,
    strategy,
    token,
    gov,
    profit_whale,
    profit_amount,
    target,
    force_claim=True,
):

    # reset everything with a sleep and mine
    increase_time(chain, 1)

    # add in any custom logic needed here, for instance with router strategy (also reason we have a destination strategy).
    # also add in any custom logic needed to get raw reward assets to the strategy (like for liquity)

    ####### ADD LOGIC AS NEEDED FOR CLAIMING/SENDING REWARDS TO STRATEGY #######
    # usually this is automatic, but it may need to be externally triggered

    # use which_strategy for our target value
    vault = Contract(
        strategy.vault(), abi="abis/IVaultFactory045.json"
    )  # use this for when we do permissionless harvests (gov=9)

    # this should only happen with convex strategies
    if target == 0:
        # we used to earmark each time, but don't anymore since convex added logic to prevent over-harvesting
        # booster = interface.IConvexBooster(strategy.depositContract())
        # booster.earmarkRewards(strategy.pid(), sender=profit_whale)

        # when in emergency exit we don't enter prepare return, so we should manually claim rewards when withdrawing
        if strategy.emergencyExit():
            strategy.setClaimRewards(True, sender=vault.governance())
        else:
            if strategy.claimRewards():
                strategy.setClaimRewards(False, sender=vault.governance())

    # if we have no staked assets, and we are taking profit (when closing out a strategy) then we will need to ignore health check
    # we also may have profit and no assets in edge cases
    if strategy.stakedBalance() == 0:
        strategy.setDoHealthCheck(False, sender=vault.governance())
        print("\nTurned off health check!\n")

    # for PRISMA, force claims by default
    if target == 2:
        claim_or_not = strategy.claimParams()["shouldClaimRewards"]
        print("Claim or not:", claim_or_not)
        strategy.setClaimParams(force_claim, claim_or_not, sender=vault.governance())

    if gov != 9:
        tx = strategy.harvest(sender=gov)
        for log in strategy.Harvested.from_receipt(tx):
            profit = log.profit / (10 ** token.decimals())
            loss = log.loss / (10 ** token.decimals())

    if target == 4:
        assert (
            strategy.balanceOfWant() < strategy.depositInfo()["minDeposit"]
            or strategy.depositInfo()["maxSingleDeposit"]
            < strategy.estimatedTotalAssets()
        )
    else:
        assert strategy.balanceOfWant() == 0

    # our trade handler takes action, sending out rewards tokens and sending back in profit
    if use_yswaps:
        trade_handler_action(strategy, token, gov, profit_whale, profit_amount, target)

    if gov == 9:
        trade_handler_action(strategy, token, gov, profit_whale, profit_amount, target)
        return (0, 0)

    # reset everything with a sleep and mine
    increase_time(chain, 60)

    # return our profit, loss
    return (profit, loss)


# simulate the trade handler sweeping out assets and sending back profit
def trade_handler_action(
    strategy,
    token,
    gov,
    profit_whale,
    profit_amount,
    target,
):
    ####### ADD LOGIC AS NEEDED FOR SENDING REWARDS OUT AND PROFITS IN #######
    # get our tokens from our strategy
    # make sure to check here that we receive all of the rewards tokens we expect
    fxsBalance = 0
    crvBalance = 0
    cvxBalance = 0
    yprismaBalance = 0
    fxnBalance = 0

    # give accounts some ETH
    strategy.balance += 1 * 10**18

    if target != 3:  # fxn doesn't know anything but FXN
        crv = Contract(strategy.crv(), abi="abis/IERC20.json")
        crvBalance = crv.balanceOf(strategy)

        if target != 1:
            cvx = Contract(strategy.convexToken(), abi="abis/IERC20.json")
            cvxBalance = cvx.balanceOf(strategy)

        if target == 4:
            fxs = Contract(strategy.fxs(), abi="abis/IERC20.json")
            fxsBalance = fxs.balanceOf(strategy)

        if target == 2:
            yprisma = Contract(strategy.yPrisma(), abi="abis/IERC20.json")
            yprismaBalance = yprisma.balanceOf(strategy)
    else:
        fxn = Contract(strategy.fxn(), abi="abis/IERC20.json")
        fxnBalance = fxn.balanceOf(strategy)

    if crvBalance > 0:
        crv.transfer(token, crvBalance, sender=strategy)
        print("\n🌀 CRV rewards present:", crvBalance / 1e18, "\n")
        assert crv.balanceOf(strategy) == 0

    if cvxBalance > 0:
        cvx.transfer(token, cvxBalance, sender=strategy)
        print("\n🍦 CVX rewards present:", cvxBalance / 1e18, "\n")
        assert cvx.balanceOf(strategy) == 0

    if fxsBalance > 0:
        fxs.transfer(token, fxsBalance, sender=strategy)
        print("\n🌗 FXS rewards present:", fxsBalance / 1e18, "\n")
        assert fxs.balanceOf(strategy) == 0

    if yprismaBalance > 0:
        yprisma.transfer(token, yprismaBalance, sender=strategy)
        print("\n🌈 yPRISMA rewards present:", yprismaBalance / 1e18, "\n")
        assert yprisma.balanceOf(strategy) == 0

    if fxnBalance > 0:
        fxn.transfer(token, fxnBalance, sender=strategy)
        print("\n🧮 FXN rewards present:", fxnBalance / 1e18, "\n")
        assert fxn.balanceOf(strategy) == 0

    # send our profits back in
    if (
        crvBalance > 0
        or cvxBalance > 0
        or fxsBalance > 0
        or yprismaBalance > 0
        or fxnBalance > 0
    ):
        token.transfer(strategy, profit_amount, sender=profit_whale)
        print("Rewards converted into profit and returned")
        assert strategy.balanceOfWant() > 0


# do a check on our strategy and vault of choice
def check_status(
    strategy,
    vault,
):
    # check our current status
    strategy_params = vault.strategies(strategy)
    vault_assets = vault.totalAssets()
    debt_outstanding = vault.debtOutstanding(strategy)
    credit_available = vault.creditAvailable(strategy)
    total_debt = vault.totalDebt()
    share_price = vault.pricePerShare()
    strategy_debt = strategy_params["totalDebt"]
    strategy_loss = strategy_params["totalLoss"]
    strategy_gain = strategy_params["totalGain"]
    strategy_debt_ratio = strategy_params["debtRatio"]
    strategy_assets = strategy.estimatedTotalAssets()

    # print our stuff
    print("Vault Assets:", vault_assets)
    print("Strategy Debt Outstanding:", debt_outstanding)
    print("Strategy Credit Available:", credit_available)
    print("Vault Total Debt:", total_debt)
    print("Vault Share Price:", share_price)
    print("Strategy Total Debt:", strategy_debt)
    print("Strategy Total Loss:", strategy_loss)
    print("Strategy Total Gain:", strategy_gain)
    print("Strategy Debt Ratio:", strategy_debt_ratio)
    print("Strategy Estimated Total Assets:", strategy_assets, "\n")

    # print simplified versions if we have something more than dust
    token = Contract(vault.token(), abi="abis/IERC20.json")
    if vault_assets > 10:
        print(
            "Decimal-Corrected Vault Assets:", vault_assets / (10 ** token.decimals())
        )
    if debt_outstanding > 10:
        print(
            "Decimal-Corrected Strategy Debt Outstanding:",
            debt_outstanding / (10 ** token.decimals()),
        )
    if credit_available > 10:
        print(
            "Decimal-Corrected Strategy Credit Available:",
            credit_available / (10 ** token.decimals()),
        )
    if total_debt > 10:
        print(
            "Decimal-Corrected Vault Total Debt:", total_debt / (10 ** token.decimals())
        )
    if share_price > 10:
        print("Decimal-Corrected Share Price:", share_price / (10 ** token.decimals()))
    if strategy_debt > 10:
        print(
            "Decimal-Corrected Strategy Total Debt:",
            strategy_debt / (10 ** token.decimals()),
        )
    if strategy_loss > 10:
        print(
            "Decimal-Corrected Strategy Total Loss:",
            strategy_loss / (10 ** token.decimals()),
        )
    if strategy_gain > 10:
        print(
            "Decimal-Corrected Strategy Total Gain:",
            strategy_gain / (10 ** token.decimals()),
        )
    if strategy_assets > 10:
        print(
            "Decimal-Corrected Strategy Total Assets:",
            strategy_assets / (10 ** token.decimals()),
        )

    return strategy_params
