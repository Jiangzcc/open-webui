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
			redeem: '卡密兑换',
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
		redeem: {
			title: '卡密充值',
			codeLabel: '卡密',
			placeholder: '输入卡密，例如 OWC-…',
			submit: '立即兑换',
			submitting: '兑换中',
			success: '兑换成功，已到账 {{credits}} 积分',
			failed: '暂时无法兑换，请稍后重试',
			ledgerLabel: '卡密兑换'
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
			redeemCodes: '卡密',
			redeem: {
				title: '卡密批次',
				description: '生成一次性卡密、查看兑换进度并作废尚未使用的卡密。',
				create: '生成卡密',
				createTitle: '生成卡密批次',
				batchName: '批次名称',
				batchNamePlaceholder: '例如：八月体验活动',
				faceValue: '单张面值',
				quantity: '生成数量',
				expiresAt: '过期日期（可选）',
				perUserLimit: '单用户限兑（可选）',
				generate: '确认生成',
				generating: '生成中',
				createdTitle: '卡密已生成',
				copyAll: '复制全部',
				copy: '复制',
				copied: '已复制',
				downloadCsv: '下载 CSV',
				closeAfterSave: '我已安全保存，关闭',
				loadError: '无法加载卡密批次',
				createError: '无法生成卡密批次',
				expiryNotFuture: '过期时间必须晚于当前时间，请选择更晚的日期或留空',
				copyError: '复制失败，请手动选择文本复制',
				empty: '尚未生成卡密批次',
				redeemed: '已兑换',
				unused: '未使用',
				voided: '已作废',
				available: '可兑换',
				expired: '已过期',
				neverExpires: '永久有效',
				expires: '{{date}} 过期',
				perUser: '每位用户最多 {{count}} 张',
				viewDetails: '查看明细',
				voidBatch: '作废未用卡密',
				voidBatchConfirm: '确定作废此批次中所有尚未使用的卡密吗？已兑换积分不会受影响。',
				voidCode: '作废此卡',
				voidError: '无法完成作废操作',
				codes: '卡密状态',
				audit: '审计记录',
				codeHint: '卡密标识',
				status: '状态',
				redeemedBy: '兑换用户',
				noCodes: '没有卡密记录',
				noAudit: '没有审计记录',
				actions: {
					generate: '生成批次',
					redeem: '用户兑换',
					void_batch: '作废批次',
					void_code: '作废卡密'
				}
			},
			reconciliationTitle: '异常扣费对账',
			reconciliationDescription: '核查失败或状态未知但已扣费的图片和视频请求，并进行一次性补偿。',
			mockMode: '模拟',
			realFalMode: '真实 FAL',
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
			compensationConfirmTitle: '确认积分补偿',
			compensationConfirmMessage:
				'此操作将向用户 {{user}} 补偿 {{credits}} 积分。补偿仅可执行一次，请确认无误。',
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
			repair: {
				button: '台账修复',
				title: '台账修复',
				description:
					'账户余额与台账合计不一致时使用。请确认已备份数据库，然后填写事件编号与台账合计（即修复后期望余额），系统将把账户余额校准为台账合计并留下审计记录。',
				incidentId: '事件编号',
				expectedBalance: '台账合计（修复后余额）',
				note: '修复说明',
				backupConfirmed: '我已确认完成数据库备份',
				submit: '执行修复',
				saved: '台账修复已完成',
				saveError: '无法完成台账修复'
			},
			ledgerTitle: '积分流水',
			ledgerDescription: '已删除用户的审计历史仍会永久保留。',
			ledgerLoadError: '无法加载积分流水',
			userId: '用户 ID',
			userQuery: '用户名或邮箱',
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
				saved: '积分价格已保存',
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
					'按”基础价格 × 像素数 ÷ 计费单位”计算。每百万像素计费请填写 1000000。',
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
			account_ledger_mismatch: '账户与台账不一致，请先在「账户」页执行台账修复后再调整',
			provider_failed: '图片服务请求失败',
			invalid_image_size: '图片尺寸不符合模型要求',
			generation_cancelled: '图片生成已取消',
			rate_limited: '请求过于频繁，请稍后再试',
			rate_limit_exceeded: '请求过于频繁，请稍后再试',
			redeem_code_invalid: '卡密错误，请检查后重试',
			redeem_code_used: '该卡密已被使用',
			redeem_code_voided: '该卡密已被作废',
			redeem_code_expired: '该卡密已过期',
			redeem_code_limit_reached: '你已达到该批次的兑换上限',
			redeem_batch_not_found: '未找到该卡密批次'
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
			redeem: 'Redeem code',
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
		redeem: {
			title: 'Redeem code',
			codeLabel: 'Redeem code',
			placeholder: 'Enter a code, for example OWC-…',
			submit: 'Redeem now',
			submitting: 'Redeeming',
			success: '{{credits}} credits were added to your balance',
			failed: 'Unable to redeem this code right now',
			ledgerLabel: 'Code redemption'
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
			redeemCodes: 'Redeem codes',
			redeem: {
				title: 'Redeem-code batches',
				description: 'Generate one-time codes, monitor redemption, and void unused codes.',
				create: 'Generate codes',
				createTitle: 'Generate a redeem-code batch',
				batchName: 'Batch name',
				batchNamePlaceholder: 'For example: August trial campaign',
				faceValue: 'Credits per code',
				quantity: 'Number of codes',
				expiresAt: 'Expiry date (optional)',
				perUserLimit: 'Per-user limit (optional)',
				generate: 'Generate',
				generating: 'Generating',
				createdTitle: 'Codes generated',
				copyAll: 'Copy all',
				copy: 'Copy',
				copied: 'Copied',
				downloadCsv: 'Download CSV',
				closeAfterSave: 'Saved securely, close',
				loadError: 'Unable to load redeem-code batches',
				createError: 'Unable to generate redeem codes',
				expiryNotFuture: 'Expiry must be in the future; pick a later date or leave it empty',
				copyError: 'Copy failed; please select the text manually',
				empty: 'No redeem-code batches yet',
				redeemed: 'Redeemed',
				unused: 'Unused',
				voided: 'Voided',
				available: 'Available',
				expired: 'Expired',
				neverExpires: 'Never expires',
				expires: 'Expires {{date}}',
				perUser: 'Up to {{count}} per user',
				viewDetails: 'View details',
				voidBatch: 'Void unused codes',
				voidBatchConfirm: 'Void every unused code in this batch? Redeemed credits are unaffected.',
				voidCode: 'Void code',
				voidError: 'Unable to void the selected codes',
				codes: 'Code status',
				audit: 'Audit log',
				codeHint: 'Code reference',
				status: 'Status',
				redeemedBy: 'Redeemed by',
				noCodes: 'No code records',
				noAudit: 'No audit records',
				actions: {
					generate: 'Batch generated',
					redeem: 'User redeemed',
					void_batch: 'Batch voided',
					void_code: 'Code voided'
				}
			},
			reconciliationTitle: 'Abnormal charge reconciliation',
			reconciliationDescription:
				'Review failed or unknown image and video requests that were charged and compensate once.',
			mockMode: 'Mock',
			realFalMode: 'Real FAL',
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
			compensationConfirmTitle: 'Confirm credit compensation',
			compensationConfirmMessage:
				'This will compensate {{credits}} credits to user {{user}}. Compensation can only be performed once.',
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
			repair: {
				button: 'Ledger repair',
				title: 'Ledger repair',
				description:
					'Use when the account balance diverges from its ledger total. Confirm a database backup, then provide the incident id and the ledger total (the balance after repair). The account is calibrated to the ledger total and the repair is audited.',
				incidentId: 'Incident id',
				expectedBalance: 'Ledger total (balance after repair)',
				note: 'Repair note',
				backupConfirmed: 'I have confirmed a database backup',
				submit: 'Run repair',
				saved: 'Ledger repair completed',
				saveError: 'Unable to complete ledger repair'
			},
			ledgerTitle: 'Credit ledger',
			ledgerDescription: 'Audit history is retained for deleted users.',
			ledgerLoadError: 'Unable to load credit ledger',
			userId: 'User ID',
			userQuery: 'Username or email',
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
				saved: 'Credit price saved',
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
			account_ledger_mismatch:
				'Account and ledger are inconsistent; run a ledger repair on the Accounts page before adjusting',
			provider_failed: 'Image provider request failed',
			invalid_image_size: 'Image size is invalid',
			generation_cancelled: 'Image generation was cancelled',
			rate_limited: 'Too many requests; try again shortly',
			rate_limit_exceeded: 'Too many requests; try again shortly',
			redeem_code_invalid: 'The redeem code is invalid',
			redeem_code_used: 'This redeem code has already been used',
			redeem_code_voided: 'This redeem code has been voided',
			redeem_code_expired: 'This redeem code has expired',
			redeem_code_limit_reached: 'You have reached this batch’s redemption limit',
			redeem_batch_not_found: 'The redeem-code batch was not found'
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
	'provider_failed',
	'invalid_image_size',
	'generation_cancelled',
	'rate_limited',
	'rate_limit_exceeded',
	'redeem_code_invalid',
	'redeem_code_used',
	'redeem_code_voided',
	'redeem_code_expired',
	'redeem_code_limit_reached',
	'redeem_batch_not_found'
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
		typeof (error as CreditApiError).code === 'string'
	) {
		const creditError = error as CreditApiError;
		if (creditErrorCodes.has(creditError.code)) {
			return i18n.t(`credits.errors.${creditError.code}`);
		}
		// 白名单外的错误码：后端附带的具体原因（如修复校验失败详情）优先于
		// 组件回退文案，避免把校验/限流错误误报成「积分服务暂不可用」。
		const reason = creditError.context?.reason;
		if (typeof reason === 'string' && reason) {
			return reason;
		}
	}

	return i18n.t(fallbackKey);
};
