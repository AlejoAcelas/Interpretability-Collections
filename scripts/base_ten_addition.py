# %%
import sys

from src.dataset.tokenizer import BaseTenAdditionTokenizer
from src.dataset.dataset import BaseTenAdditionDataConstructor
from src.dataset.discriminators import BaseTenAdditionTokenCriteriaCollection
from src.dataset.generators import BaseTenAdditionTokenGenerator
from src.experiments.plot import DataPlotter
from src.train.train import load_model

import einops
import torch
import plotly.express as px

sys.path.append('/home/alejo/Projects')
from path_patching import path_patch, act_patch, Node, IterNode
from my_plotly_utils import imshow
from new_plotly_utils import bar, box, histogram, line, scatter, violin

# %%
data_constructor = BaseTenAdditionDataConstructor(n_digits_addend=4)
model = load_model('final/addition4-l2_h2_d64_m4-1000.pt', data_constructor)
plotter = DataPlotter(data_constructor, model)

tokenizer: BaseTenAdditionTokenizer = data_constructor.tokenizer
generators: BaseTenAdditionTokenGenerator = data_constructor.generators
discriminators: BaseTenAdditionTokenCriteriaCollection = data_constructor.discriminators

LABEL_POS = tokenizer.get_label_pos()
ADDENDS_POS = tokenizer.get_numeric_pos()

# %% SVD Scatter Plots

tokens = data_constructor.gen_tokens(10)
tokens = generators.gen_carry_tokens(10, carry_depth=3)
plotter.plot_attn_patterns(tokens)
# %%
layer, head = 0, 0
data_constructor.set_seed(0)

tokens = data_constructor.gen_tokens(500)
_, cache = model.run_with_cache(tokens)

pos_sum = tokenizer.get_label_pos()
head_result = cache['result', layer][:, pos_sum, head]
# head_result = cache['mlp_out', layer][:, pos_sum]

svd_head = plotter.get_svd_components_per_dimension(head_result)
svd_head_combined = plotter.get_svd_components_across_dimensions(head_result)

addend1, addend2 = tokenizer.get_addends_from_tokens(tokens)
sum_with_no_carry = addend1 + addend2
sum_with_carry = discriminators.sum_tokens(tokens)

# %%
pos_to_plot = 1
U, S, V = head_result[:, pos_to_plot].svd()
line(S, labels=dict(x='Singular Value', y='Value'), title=f'Singular Values for H{layer}.{head} at position {pos_to_plot}')


# %%
pos_to_plot = 1
token_addend1 = addend1[:, pos_to_plot]
token_addend2 = addend2[:, pos_to_plot]

# scatter(
#     svd_head[:, pos_to_plot, 1], svd_head[:, pos_to_plot, 0],
#     dim_labels=['Batch'], color=token_addend1, addend2=token_addend2,
#     labels=dict(color=f'Addend 1 at {pos_to_plot}'),
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}'
# )
# scatter(
#     svd_head[:, pos_to_plot, 1], svd_head[:, pos_to_plot, 0],
#     dim_labels=['Batch'], color=token_addend2, addend1=token_addend1,
#     labels=dict(color=f'Addend 2 at {pos_to_plot}'),
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}'
# )
scatter(
    svd_head[:, pos_to_plot, 1], svd_head[:, pos_to_plot, 0],
    dim_labels=['Batch'], color=sum_with_no_carry[:, pos_to_plot], 
    addend1=token_addend1, addend2=token_addend2,
    labels=dict(color=f'Sum at {pos_to_plot}'),
    title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
    color_continuous_scale='Turbo',
)

scatter(
    svd_head[:, pos_to_plot, :, None], svd_head[:, pos_to_plot, None, :],
    dim_labels=['Batch', 'SVD Comp1', 'SVD Comp2'], 
    color=sum_with_no_carry[:, pos_to_plot, None, None], 
    facet_col='SVD Comp1', facet_row='SVD Comp2',
    labels=dict(color=f'Sum at {pos_to_plot}'),
    title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
    color_continuous_scale='Turbo', height=1000, width=1000,
)

scatter(
    svd_head_combined[:, :4, :, None], svd_head_combined[:, :4, None, :],
    dim_labels=['Batch', 'Sum Position', 'SVD Comp1', 'SVD Comp2'], 
    color=sum_with_no_carry[:, :, None, None], 
    facet_col='SVD Comp1', facet_row='SVD Comp2',
    labels=dict(color=f'Sum at {pos_to_plot}'),
    title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
    color_continuous_scale='Turbo', height=1000, width=1000,
)

# scatter(
#     svd_head[:, pos_to_plot, :, None], svd_head[:, pos_to_plot, None, :],
#     dim_labels=['Batch', 'SVD Comp1', 'SVD Comp2'], 
#     color=sum_with_carry[:, pos_to_plot, None, None], 
#     facet_col='SVD Comp1', facet_row='SVD Comp2',
#     labels=dict(color=f'Sum at {pos_to_plot}'),
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
#     color_continuous_scale='Turbo', height=1000, width=1000,
# )
# %%


layer, head = 0, 1
data_constructor.set_seed(0)

tokens = data_constructor.gen_tokens(100)
_, cache = model.run_with_cache(tokens)

pos_sum = tokenizer.get_label_pos()
head_result = cache['result', layer][:, pos_sum, head]
# head_result = cache['mlp_out', layer][:, pos_sum]

svd_head = plotter.get_svd_components_per_dimension(head_result)
svd_head_combined = plotter.get_svd_components_across_dimensions(head_result)

carry_matrix = discriminators._get_carry_matrix(tokens)
addend1, addend2 = tokenizer.get_addends_from_tokens(tokens)
sum_with_no_carry = addend1 + addend2
sum_with_carry = discriminators.sum_tokens(tokens)

# %%
pos_to_plot = 1
U, S, V = head_result[:, pos_to_plot].svd()
line(S, labels=dict(x='Singular Value', y='Value'), title=f'Singular Values for H{layer}.{head} at position {pos_to_plot}')


# %%
pos_to_plot = 1


scatter(
    svd_head[:, pos_to_plot, 1], svd_head[:, pos_to_plot, 0],
    dim_labels=['Batch'], color=sum_with_carry[:, pos_to_plot],
    title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
    color_continuous_scale='Turbo',
)

scatter(
    svd_head[:, pos_to_plot, :, None], svd_head[:, pos_to_plot, None, :],
    dim_labels=['Batch', 'SVD Comp1', 'SVD Comp2'], 
    color=sum_with_carry[:, pos_to_plot, None, None], 
    facet_col='SVD Comp1', facet_row='SVD Comp2',
    labels=dict(color=f'Sum at {pos_to_plot}'),
    title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
    color_continuous_scale='Turbo', height=1000, width=1000,
)


# scatter(
#     svd_head[:, pos_to_plot, 1], svd_head[:, pos_to_plot, 0],
#     dim_labels=['Batch'], color=carry_matrix[:, pos_to_plot - 1 , 0], 
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
#     color_continuous_scale='Turbo',
# )

# scatter(
#     svd_head[:, pos_to_plot, :, None], svd_head[:, pos_to_plot, None, :],
#     dim_labels=['Batch', 'SVD Comp1', 'SVD Comp2'], 
#     color=carry_matrix[:, pos_to_plot, 0, None, None], 
#     facet_col='SVD Comp1', facet_row='SVD Comp2',
#     labels=dict(color=f'Sum at {pos_to_plot}'),
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
#     color_continuous_scale='Turbo', height=1000, width=1000,
# )

# scatter(
#     svd_head_combined[:, :4, :, None], svd_head_combined[:, :4, None, :],
#     dim_labels=['Batch', 'Sum Position', 'SVD Comp1', 'SVD Comp2'], 
#     color=sum_with_no_carry[:, :, None, None], 
#     facet_col='SVD Comp1', facet_row='SVD Comp2',
#     labels=dict(color=f'Sum at {pos_to_plot}'),
#     title=f'SVD Components for H{layer}.{head} at position {pos_to_plot}',
#     color_continuous_scale='Turbo', height=1000, width=1000,
# )

# %% Path Patching
from src.utils import compute_cross_entropy_loss

batch_size = 500

data_constructor.set_seed(0)

orig_tokens = data_constructor.gen_tokens(batch_size)
alter_tokens = data_constructor.gen_tokens(batch_size)

orig_labels = data_constructor.get_token_labels(orig_tokens)


loss_metric_no_reduce = lambda logits: compute_cross_entropy_loss(
    logits[:, LABEL_POS].cpu(),
    orig_labels,
    reduce='none',
)
loss_metric = lambda logits: loss_metric_no_reduce(logits).mean().item()
orig_loss = loss_metric(model(orig_tokens))
random_loss = loss_metric(model(orig_tokens[torch.randperm(batch_size)]))
recovered_loss_metric = lambda logits: ((random_loss - loss_metric(logits)) /
                                         (random_loss - orig_loss))

# %%
patch_pattern_by_head = act_patch(
    model=model,
    orig_input=orig_tokens,
    new_input=alter_tokens,
    patching_nodes=IterNode('pattern'),
    patching_metric=recovered_loss_metric,
)

imshow(
    patch_pattern_by_head['pattern'],
    labels=dict(x='Head', y='Layer'),
    title='Loss after randomly swapping attn pattern with another sequence',
)

# %%
addends_pos_with_batch_dim = einops.repeat(
    ADDENDS_POS, 'pos -> batch pos', batch=batch_size
)

patch_resid = act_patch(
    model=model,
    orig_input=orig_tokens,
    new_input=alter_tokens,
    patching_nodes=IterNode('resid_pre', seq_pos=addends_pos_with_batch_dim),
    patching_metric=recovered_loss_metric,
)

bar(
    patch_resid['resid_pre'],
    labels=dict(index='Layer', y='Loss'),
    title='Loss after randomly swapping resid_pre at addends <br>with another sequence',
)

# %%

batch_size = 200
alter_to_orig_ratio = 5

data_constructor.set_seed(0)

orig_tokens = data_constructor.gen_tokens(batch_size)
orig_tokens = einops.repeat(
    orig_tokens, 'batch pos -> (batch repeat) pos',
    repeat=alter_to_orig_ratio
)
alter_tokens = data_constructor.gen_tokens(batch_size * alter_to_orig_ratio)

orig_labels = data_constructor.get_token_labels(orig_tokens)

loss_metric_multi_patch = lambda logits: einops.reduce(
    loss_metric_no_reduce(logits), '(batch repeat) pos -> batch pos',
    repeat=alter_to_orig_ratio,
    reduction='mean',
)

patch_z_by_head = act_patch(
    model=model,
    orig_input=orig_tokens,
    new_input=alter_tokens,
    patching_nodes=IterNode('z'),
    patching_metric=loss_metric_multi_patch,
)

head_names_list = [f'Head {layer}.{head}' for layer in range(2) for head in range(2)]

for i, head_name in enumerate(head_names_list):
    patch_loss_head = patch_z_by_head['z'][i]
    highest_loss_inputs = patch_z_by_head['z'][1].sum(dim=1).topk(30).indices
    imshow(
        patch_loss_head[highest_loss_inputs].T,
        labels=dict(x='Batch', y='Position'),
        title=f'Loss for {head_name} after randomly swapping hook_z',
    )
print(orig_tokens[highest_loss_inputs][:, ADDENDS_POS])
print(discriminators.sum_tokens(orig_tokens[highest_loss_inputs]))


# %%