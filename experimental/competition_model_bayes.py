import competition_models
import torch
import pyro
import pyro.distributions as dist
import pyro.infer
import pyro.optim
from torch.distributions import constraints


class CompetitionModelGraphical(competition_models.CompetitionModel):

    def __init__(self, systems: list[str]):
        self.systems = systems
        self.system_to_id = {sys: i for i, sys in enumerate(systems)}
        self.id_to_system = {i: sys for i, sys in enumerate(systems)}
        self.match_data = []

    def beta_skill_model(player_a_ids, player_b_ids, scores):
        """
        Models a 1v1 match where the outcome is a continuous score
        in [0, 1] representing player A's win-share.

        :param player_a_ids: 1D tensor of Player A's IDs
        :param player_b_ids: 1D tensor of Player B's IDs
        :param scores: 1D tensor of Player A's scores (e.g., 0.7)
        """
        num_players = int(max(player_a_ids.max(), player_b_ids.max())) + 1

        # --- Priors ---
        # Priors for all player skills
        with pyro.plate("players", num_players):
            skills = pyro.sample("skill", dist.Normal(0.0, 1.0))

        # --- Global Concentration Parameter ---
        # This single parameter controls the "variance" of all matches.
        # We initialize it at 2.0 (like a Beta(1,1) uniform prior
        # if mean is 0.5) and constrain it to be positive.
        phi = pyro.param(
            "phi",
            torch.tensor(2.0),
            constraint=constraints.positive,
        )

        # --- Likelihood ---
        with pyro.plate("matches", len(player_a_ids)):
            # Get skills for each match
            s_a = skills[player_a_ids]
            s_b = skills[player_b_ids]

            # 1. Calculate the expected mean score for Player A
            skill_diff = s_a - s_b
            mean_score = torch.sigmoid(skill_diff)

            # 2. Convert (mean, concentration) to (alpha, beta)
            # We clamp to avoid numerical issues if mean is exactly 0 or 1
            mean_score = mean_score.clamp(min=1e-5, max=1.0 - 1e-5)

            alpha = mean_score * phi
            beta = (1.0 - mean_score) * phi

            # 3. Observe the scores using the Beta distribution
            pyro.sample("outcome", dist.Beta(alpha, beta), obs=scores)

    def beta_skill_guide(player_a_ids, player_b_ids, scores):
        """
        Variational approximation (guide)
        We learn a mean and std dev for each player's skill
        """
        num_players = int(max(player_a_ids.max(), player_b_ids.max())) + 1

        # Learnable parameters for skill means
        skill_loc = pyro.param("skill_loc", torch.zeros(num_players))
        # Learnable parameters for skill std devs (must be positive)
        skill_scale = pyro.param(
            "skill_scale",
            torch.ones(num_players),
            constraint=dist.constraints.positive,
        )

        with pyro.plate("players", num_players):
            # Sample from the approximate posterior
            pyro.sample("skill", dist.Normal(skill_loc, skill_scale))

    # --- Example Data ---
    # (Player A, Player B, Score for A)
    # Player 0 (good) vs Player 1 (avg) -> 0 wins 70%
    # Player 0 (good) vs Player 2 (bad) -> 0 wins 90%
    # Player 1 (avg) vs Player 2 (bad) -> 1 wins 75%
    # Player 2 (bad) vs Player 0 (good) -> 2 wins 15% (0 wins 85%)

    player_a_ids = torch.tensor([0, 0, 1, 2])
    player_b_ids = torch.tensor([1, 2, 2, 0])
    scores = torch.tensor([0.70, 0.90, 0.75, 0.15])

    # --- Run SVI ---
    pyro.clear_param_store()
    svi = pyro.infer.SVI(
        beta_skill_model,
        beta_skill_guide,
        pyro.optim.ClippedAdam({"lr": 0.01}),
        loss=pyro.infer.Trace_ELBO(),
    )

    print("Training Beta Regression skill model...")
    for step in range(3000):
        loss = svi.step(player_a_ids, player_b_ids, scores)
        if step % 500 == 0:
            print(f"Step {step}: ELBO Loss = {loss:.2f}")

    print("Training complete.")

    # --- Get results ---
    skill_means = pyro.param("skill_loc").detach()
    skill_std_devs = pyro.param("skill_scale").detach()
    learned_phi = pyro.param("phi").detach()

    print("\n--- Learned Skills (Logit-Scale) ---")
    for i in range(len(skill_means)):
        print(f"Player {i}: {skill_means[i]:.2f} +/- {skill_std_devs[i]:.2f}")

    print(f"\n--- Learned Game Consistency ---")
    print(f"Concentration (phi): {learned_phi:.2f}")
