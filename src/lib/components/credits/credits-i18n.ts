import type { i18n as I18n } from 'i18next';
import { get, type Readable } from 'svelte/store';

import type { CreditApiError } from '$lib/apis/credits';

const zh = {
	credits: {
		balance: '积分',
		unavailable: '积分服务暂不可用',
		ledger: '积分明细',
		quote: '预计消耗',
		insufficient: '积分不足',
		unconfigured: '暂未配置积分价格',
		exempt: '管理员免积分',
		adjustment: '积分调整',
		prices: '积分价格',
		dimensions: '计费维度',
		filters: {
			all: '全部',
			income: '收入',
			consumption: '消费',
			adjustment: '调整'
		},
		status: {
			failedCharged: '生成失败，已按规则扣费'
		},
		reasons: {
			offline_recharge: '线下充值',
			promotion_gift: '活动赠送',
			manual_refund: '人工退款',
			accounting_correction: '账务更正',
			violation_deduction: '违规扣减',
			other: '其他'
		},
		entryTypes: {
			consumption: '消费',
			admin_adjustment: '管理员调整',
			system_adjustment: '系统调整'
		},
		serviceTypes: {
			image: '图片',
			video: '视频'
		},
		actions: {
			'text-to-image': '文生图',
			'image-to-image': '图生图',
			'text-to-video': '文生视频',
			'image-to-video': '图生视频',
			'video-to-video': '视频生视频'
		},
		dimensionKeys: {
			size: '尺寸',
			resolution: '分辨率',
			aspect_ratio: '宽高比',
			quality: '质量',
			image_count: '图片数量',
			duration: '时长',
			audio_mode: '音频模式',
			pixel_count: '像素数'
		},
		common: {
			unit: '积分',
			close: '关闭',
			retry: '重试',
			from: '开始日期',
			to: '结束日期',
			applyFilters: '应用筛选',
			loading: '加载中',
			loadMore: '加载更多',
			noLedgerEntries: '未找到积分流水',
			createdAt: '创建时间',
			amount: '数量',
			type: '类型',
			resource: '资源',
			user: '用户',
			balance: '余额',
			actions: '操作',
			deletedUser: '已删除用户',
			confirm: '确认',
			cancel: '取消',
			saving: '保存中',
			save: '保存',
			delete: '删除',
			edit: '编辑',
			new: '新建',
			enabled: '已启用',
			disabled: '已禁用',
			remove: '移除',
			value: '值',
			multiplier: '倍率',
			action: '操作'
		},
		admin: {
			management: '积分管理',
			description: '管理账户、流水记录、定价规则和支持的计费维度。',
			accounts: '账户',
			ledger: '永久流水',
			pricingTab: '价目',
			dimensions: '维度',
			reconciliation: '异常对账',
			reconciliationTitle: '异常扣费对账',
			reconciliationDescription: '核查失败或状态未知但已扣费的图片请求，并进行一次性补偿。',
			reconciliationEmpty: '没有待处理的异常扣费',
			reconciliationLoadError: '无法加载异常扣费记录',
			allStatuses: '全部异常状态',
			allCompensation: '全部补偿状态',
			uncompensated: '未补偿',
			compensate: '补偿',
			compensated: '已补偿',
			compensationSaved: '补偿已入账',
			compensationError: '无法完成补偿',
			compensationNote: '补偿说明（可选）',
			accountsTitle: '积分账户',
			accountsDescription: '搜索当前用户并调整其可用积分余额。',
			accountsSearch: '按姓名或邮箱搜索',
			accountsEmpty: '未找到积分账户',
			accountsLoadError: '无法加载积分账户',
			adjust: '调整',
			adjustCredits: '调整积分',
			adjustment: {
				saved: '积分调整已保存',
				saveError: '无法保存积分调整',
				confirmTitle: '确认积分调整',
				confirmMessage: '此操作将永久更新所选用户的积分余额。',
				title: '积分调整',
				direction: '调整方向',
				increase: '增加',
				decrease: '减少',
				reason: '原因',
				note: '备注'
			},
			ledgerTitle: '积分流水',
			ledgerDescription: '已删除用户的审计历史仍会永久保留。',
			ledgerLoadError: '无法加载积分流水',
			userId: '用户 ID',
			allTypes: '全部类型',
			allReasons: '全部原因',
			modelOrResource: '模型或资源',
			pricingTitle: '积分价格',
			pricingDescription: '为每个服务、资源和操作创建已启用的定价规则。',
			pricingEmpty: '尚未配置积分价格',
			pricingLoadError: '无法加载积分价格',
			pricingSaveError: '无法保存积分价格',
			pricingDeleteError: '无法删除积分价格',
			pricing: {
				deleteTitle: '删除积分价格',
				deleteMessage: '删除后，新积分计算将不再使用此价格。',
				service: '服务',
				basePrice: '基础价格',
				editTitle: '编辑积分价格',
				newTitle: '新建积分价格',
				serviceType: '服务类型',
				resourceId: '资源 ID',
				addDimension: '添加维度',
				addMapping: '添加映射',
				dimensionKey: '维度键',
				quantityDescription: '按请求的正数数量乘以价格。',
				unitSize: '计费单位（像素）',
				proportionalDescription:
					'按“基础价格 × 像素数 ÷ 计费单位”计算。每百万像素计费请填写 1000000。',
				ruleKinds: {
					exact_map: '精确映射',
					numeric_tier: '数值分层',
					unit_blocks: '单位分块',
					proportional: '按单位线性计费',
					quantity: '数量'
				}
			},
			dimensionsTitle: '计费维度',
			dimensionsDescription: '服务器注册表定义了可定价的维度键和规则类型。',
			dimensionsNotice: '这里只定义允许参与计价的维度；具体模型价格仍需在积分价格中配置。',
			dimensionsEmpty: '未注册计费维度',
			dimensionsLoadError: '无法加载计费维度',
			imageService: '图片',
			videoService: '视频'
		},
		validation: {
			positiveWholeNumber: '请输入正整数',
			explainAdjustment: '请说明本次调整',
			serviceType: '请输入服务类型',
			resourceId: '请输入资源 ID',
			action: '请输入操作',
			positivePrice: '请输入大于零的价格',
			uniqueDimensions: '每个计费维度只能配置一次',
			validMultipliers: '每个维度都需要有效的正数倍率'
		},
		errors: {
			invalidDateRange: '结束日期不能早于开始日期',
			price_not_configured: '未配置积分价格',
			price_rule_incomplete: '积分定价规则不完整',
			insufficient_credits: '积分不足',
			idempotency_key_conflict: '该请求与已有请求冲突，请重试',
			usage_processing: '积分请求仍在处理中',
			credit_account_conflict: '积分账户已被并发更新，请重试',
			invalid_adjustment: '积分调整无效',
			credit_service_unavailable: '积分服务暂不可用',
			provider_failed: '图片服务请求失败'
		}
	}
};

const en = {
	credits: {
		balance: 'Credits',
		unavailable: 'Credit service is unavailable',
		ledger: 'Credit ledger',
		quote: 'Estimated credits',
		insufficient: 'Insufficient credits',
		unconfigured: 'Credit price is not configured',
		exempt: 'Admin exempt',
		adjustment: 'Credit adjustment',
		prices: 'Credit prices',
		dimensions: 'Billing dimensions',
		filters: {
			all: 'All',
			income: 'Income',
			consumption: 'Consumption',
			adjustment: 'Adjustments'
		},
		status: {
			failedCharged: 'Generation failed; credits were charged according to the pricing rule'
		},
		reasons: {
			offline_recharge: 'Offline recharge',
			promotion_gift: 'Promotion gift',
			manual_refund: 'Manual refund',
			accounting_correction: 'Accounting correction',
			violation_deduction: 'Violation deduction',
			other: 'Other'
		},
		entryTypes: {
			consumption: 'Consumption',
			admin_adjustment: 'Admin adjustment',
			system_adjustment: 'System adjustment'
		},
		serviceTypes: {
			image: 'Image',
			video: 'Video'
		},
		actions: {
			'text-to-image': 'Text to image',
			'image-to-image': 'Image to image',
			'text-to-video': 'Text to video',
			'image-to-video': 'Image to video',
			'video-to-video': 'Video to video'
		},
		dimensionKeys: {
			size: 'Size',
			resolution: 'Resolution',
			aspect_ratio: 'Aspect ratio',
			quality: 'Quality',
			image_count: 'Image count',
			duration: 'Duration',
			audio_mode: 'Audio mode',
			pixel_count: 'Pixel count'
		},
		common: {
			unit: 'credits',
			close: 'Close',
			retry: 'Retry',
			from: 'From',
			to: 'To',
			applyFilters: 'Apply filters',
			loading: 'Loading',
			loadMore: 'Load more',
			noLedgerEntries: 'No ledger entries found',
			createdAt: 'Created at',
			amount: 'Amount',
			type: 'Type',
			resource: 'Resource',
			user: 'User',
			balance: 'Balance',
			actions: 'Actions',
			deletedUser: 'Deleted user',
			confirm: 'Confirm',
			cancel: 'Cancel',
			saving: 'Saving',
			save: 'Save',
			delete: 'Delete',
			edit: 'Edit',
			new: 'New',
			enabled: 'Enabled',
			disabled: 'Disabled',
			remove: 'Remove',
			value: 'Value',
			multiplier: 'Multiplier',
			action: 'Action'
		},
		admin: {
			management: 'Credit management',
			description:
				'Manage accounts, ledger history, price rules, and supported billing dimensions.',
			accounts: 'Accounts',
			ledger: 'Permanent ledger',
			pricingTab: 'Pricing',
			dimensions: 'Dimensions',
			reconciliation: 'Reconciliation',
			reconciliationTitle: 'Abnormal charge reconciliation',
			reconciliationDescription:
				'Review failed or unknown image requests that were charged and compensate once.',
			reconciliationEmpty: 'No abnormal charges need attention',
			reconciliationLoadError: 'Unable to load abnormal charges',
			allStatuses: 'All abnormal statuses',
			allCompensation: 'All compensation',
			uncompensated: 'Uncompensated',
			compensate: 'Compensate',
			compensated: 'Compensated',
			compensationSaved: 'Compensation posted',
			compensationError: 'Unable to compensate this charge',
			compensationNote: 'Compensation note (optional)',
			accountsTitle: 'Credit accounts',
			accountsDescription: 'Search current users and adjust their available credit balance.',
			accountsSearch: 'Search by name or email',
			accountsEmpty: 'No credit accounts found',
			accountsLoadError: 'Unable to load credit accounts',
			adjust: 'Adjust',
			adjustCredits: 'Adjust credits',
			adjustment: {
				saved: 'Credit adjustment saved',
				saveError: 'Unable to save credit adjustment',
				confirmTitle: 'Confirm credit adjustment',
				confirmMessage: 'This will permanently update the selected user’s credit balance.',
				title: 'Credit adjustment',
				direction: 'Direction',
				increase: 'Increase',
				decrease: 'Decrease',
				reason: 'Reason',
				note: 'Note'
			},
			ledgerTitle: 'Credit ledger',
			ledgerDescription: 'Audit history is retained for deleted users.',
			ledgerLoadError: 'Unable to load credit ledger',
			userId: 'User ID',
			allTypes: 'All types',
			allReasons: 'All reasons',
			modelOrResource: 'Model or resource',
			pricingTitle: 'Credit prices',
			pricingDescription: 'Create enabled pricing rules for each service, resource, and action.',
			pricingEmpty: 'No credit prices configured',
			pricingLoadError: 'Unable to load credit prices',
			pricingSaveError: 'Unable to save credit price',
			pricingDeleteError: 'Unable to delete credit price',
			pricing: {
				deleteTitle: 'Delete credit price',
				deleteMessage: 'This price will no longer be available for new credit calculations.',
				service: 'Service',
				basePrice: 'Base price',
				editTitle: 'Edit credit price',
				newTitle: 'New credit price',
				serviceType: 'Service type',
				resourceId: 'Resource ID',
				addDimension: 'Add dimension',
				addMapping: 'Add mapping',
				dimensionKey: 'Dimension key',
				quantityDescription: 'Multiplies price by the requested positive quantity.',
				unitSize: 'Billing unit (pixels)',
				proportionalDescription:
					'Calculates base price × pixel count ÷ billing unit. Enter 1000000 for per-megapixel pricing.',
				ruleKinds: {
					exact_map: 'Exact map',
					numeric_tier: 'Numeric tier',
					unit_blocks: 'Unit blocks',
					proportional: 'Proportional units',
					quantity: 'Quantity'
				}
			},
			dimensionsTitle: 'Billing dimensions',
			dimensionsDescription:
				'The server registry defines the dimension keys and rule types that may be priced.',
			dimensionsNotice:
				'This registry only defines which dimensions may affect pricing; configure each model price separately.',
			dimensionsEmpty: 'No billing dimensions registered',
			dimensionsLoadError: 'Unable to load billing dimensions',
			imageService: 'Image',
			videoService: 'Video'
		},
		validation: {
			positiveWholeNumber: 'Enter a positive whole number',
			explainAdjustment: 'Explain this adjustment',
			serviceType: 'Enter a service type',
			resourceId: 'Enter a resource ID',
			action: 'Enter an action',
			positivePrice: 'Enter a positive decimal price',
			uniqueDimensions: 'Each billing dimension can only be configured once',
			validMultipliers: 'Each dimension needs valid positive multipliers'
		},
		errors: {
			invalidDateRange: 'End date cannot be earlier than start date',
			price_not_configured: 'Price is not configured',
			price_rule_incomplete: 'Price rule is incomplete',
			insufficient_credits: 'Insufficient credits',
			idempotency_key_conflict: 'Idempotency key conflicts with another request',
			usage_processing: 'Usage request is still processing',
			credit_account_conflict: 'Credit account was updated concurrently',
			invalid_adjustment: 'Credit adjustment is invalid',
			credit_service_unavailable: 'Credit service is unavailable',
			provider_failed: 'Image provider request failed'
		}
	}
};

type CreditI18n = I18n | Readable<I18n>;

const creditErrorCodes = new Set([
	'price_not_configured',
	'price_rule_incomplete',
	'insufficient_credits',
	'idempotency_key_conflict',
	'usage_processing',
	'credit_account_conflict',
	'invalid_adjustment',
	'credit_service_unavailable',
	'provider_failed'
]);

export const registerCreditTranslations = (contextI18n: CreditI18n) => {
	const i18n = 'addResourceBundle' in contextI18n ? contextI18n : get(contextI18n);
	i18n.addResourceBundle('zh-CN', 'translation', zh, true, false);
	i18n.addResourceBundle('en-US', 'translation', en, true, false);
};

export const translateCreditApiError = (
	i18n: I18n,
	error: unknown,
	fallbackKey: string
): string => {
	if (
		typeof error === 'object' &&
		error !== null &&
		'code' in error &&
		typeof (error as CreditApiError).code === 'string' &&
		creditErrorCodes.has((error as CreditApiError).code)
	) {
		return i18n.t(`credits.errors.${(error as CreditApiError).code}`);
	}

	return i18n.t(fallbackKey);
};
